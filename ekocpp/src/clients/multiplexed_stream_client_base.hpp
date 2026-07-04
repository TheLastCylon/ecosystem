#pragma once

#include <atomic>
#include <chrono>
#include <memory>
#include <mutex>
#include <optional>
#include <type_traits>
#include <unordered_map>
#include <utility>

#include <asio/experimental/concurrent_channel.hpp>

#include "client_base.hpp"
#include "../data_transfer_objects/span_key.hpp"

template <typename SocketType> class MultiplexedStreamClientBase;

// Defined in multiplexed_stream_client_base.cpp. Free functions, not members --
// same reason PersistentStreamClientBase's run_heartbeat_loop is a free
// function: a member-function coroutine's frame stores an implicit `this`,
// which would dangle if this object were destroyed while the coroutine is
// suspended.
template <typename SocketType>
asio::awaitable<void> run_heartbeat_loop(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self);

template <typename SocketType>
asio::awaitable<void> run_reader_loop(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self);

template <typename SocketType>
asio::awaitable<void> run_staleness_sweep_loop(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self);

// Full design history and rationale: documentation/multiplexed_stream_client.md
// and documentation/sending_patterns.md.
//
// One connection, held open indefinitely (see multiplexed_stream_client.md's
// "Lifecycle" section for why -- no idle-timeout, unlike an earlier discarded
// draft of this design) -- but unlike PersistentStreamClientBase, many
// send_message() calls can be genuinely in flight at once: a write-lock
// serialises only the write itself, and a background reader loop demuxes
// each incoming frame to its caller via the SpanKey already present in every
// response header. BufferedSender is the intended (and, for now, only)
// caller -- see sending_patterns.md for why UDP is excluded from this family
// entirely and why Transient clients need no equivalent.
//
// Must be held via std::shared_ptr (enable_shared_from_this) -- same
// weak_ptr/start()/stop() lifecycle discipline as PersistentStreamClientBase.
template <typename SocketType>
class MultiplexedStreamClientBase : public ClientBase,
                                     public std::enable_shared_from_this<MultiplexedStreamClientBase<SocketType>> {
public:
    explicit MultiplexedStreamClientBase(
        asio::any_io_executor     executor,
        std::chrono::milliseconds timeout                   = std::chrono::seconds{5},
        std::chrono::milliseconds heartbeat_period           = std::chrono::seconds{60},
        int                       max_retries                = 3,
        std::chrono::milliseconds retry_delay                = std::chrono::milliseconds{100},
        std::chrono::milliseconds staleness_sweep_period      = std::chrono::seconds{30},
        std::chrono::milliseconds staleness_warning_threshold = std::chrono::seconds{60}
    );

    // Call once, after construction, to start the background heartbeat and
    // staleness-sweep loops. Not done in the constructor -- shared_from_this()/
    // weak_from_this() are unsafe to call before the object is fully owned
    // by a shared_ptr.
    void start();

    // Co_await before releasing the last shared_ptr to this client, to
    // confirm both background loops have actually exited before teardown.
    asio::awaitable<void> stop();

protected:
    virtual asio::awaitable<SocketType> open_connection() = 0;

    asio::awaitable<std::vector<uint8_t>> send_message_retry_loop(std::vector<uint8_t> request) override;

private:
    // Completion signature: (error_code, response_frame). An empty error_code
    // with a non-empty frame is success; a set error_code means the reader
    // loop failed this entry out because the connection died before a real
    // response arrived (see fail_all_outstanding below).
    using DemuxChannel = asio::experimental::concurrent_channel<void(std::error_code, std::vector<uint8_t>)>;

    friend asio::awaitable<void> run_heartbeat_loop<SocketType>(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self);
    friend asio::awaitable<void> run_reader_loop<SocketType>(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self);
    friend asio::awaitable<void> run_staleness_sweep_loop<SocketType>(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self);

    asio::awaitable<void> do_heartbeat();

    // Guarded by connect_permit_ (an async mutex, same single-slot-channel
    // shape as write_permit_/send_permit_ elsewhere) -- NOT optional here the
    // way it might look at a glance. PersistentStreamClientBase's
    // send_permit_ guards the whole round trip, which serialises
    // ensure_connected() as a free side effect; write_permit_ below guards
    // only the write, so multiple callers can now race into
    // ensure_connected() concurrently on a fresh disconnect. Without its own
    // guard, that race can open two connections and spawn two reader loops
    // for what should be one. See multiplexed_stream_client.md.
    asio::awaitable<void> ensure_connected();

    // Fails every outstanding demux entry at once (a dead connection takes
    // out everything in flight on it, not just whichever caller happened to
    // notice first) and clears the map. Plain synchronous function -- no
    // co_await, callable from a catch block.
    void fail_all_outstanding(std::error_code ec);

    asio::any_io_executor      executor_;
    std::chrono::milliseconds  timeout_;
    std::chrono::milliseconds  heartbeat_period_;
    std::chrono::milliseconds  staleness_sweep_period_;
    std::chrono::milliseconds  staleness_warning_threshold_;

    std::atomic<bool>          stopping_{false};
    bool                       connected_ = false;
    std::optional<SocketType>  socket_;

    asio::steady_timer heartbeat_timer_;
    asio::steady_timer staleness_sweep_timer_;
    asio::experimental::concurrent_channel<void(std::error_code)> heartbeat_done_;
    asio::experimental::concurrent_channel<void(std::error_code)> staleness_sweep_done_;

    // Guards only the write itself -- the one real semantic change from
    // PersistentStreamClientBase's send_permit_, which guards the entire
    // round trip. Acquire = async_receive, release = try_send.
    asio::experimental::concurrent_channel<void(std::error_code)> write_permit_;

    // Async mutex around ensure_connected()'s body -- see that method's
    // comment above.
    asio::experimental::concurrent_channel<void(std::error_code)> connect_permit_;

    struct DemuxEntry {
        std::shared_ptr<DemuxChannel> channel;
        std::chrono::steady_clock::time_point registered_at;
        bool warned = false; // staleness sweep logs once per entry, not every sweep
    };

    std::mutex                                    demux_mutex_;
    std::unordered_map<SpanKey, DemuxEntry>        demux_map_;
};

// Detection idiom -- true for a type derived from MultiplexedStreamClientBase<SocketType>
// for ANY SocketType, not just the two instantiated today (asio::ip::tcp::socket,
// asio::local::stream_protocol::socket). Used to constrain BufferedSender and
// ApplicationBase::register_buffered_sender at compile time: BufferedSender's
// contract (retried, eventually-delivered, individually-acknowledged) requires a
// reliable, ordered transport, which by construction only a
// MultiplexedStreamClientBase-derived type provides -- a plain UDPClient (or any
// future MultiplexedUDPClient) is excluded automatically, not by a special case
// someone has to remember. See sending_patterns.md's "UDP: excluded, not just
// deprioritised" section.
template <typename SocketType>
std::true_type is_multiplexed_stream_client(const MultiplexedStreamClientBase<SocketType>*);
std::false_type is_multiplexed_stream_client(...);

// A type satisfies MultiplexedClient either by genuinely deriving from
// MultiplexedStreamClientBase (the real production path -- MultiplexedTCPClient/
// MultiplexedUDSClient), or by explicitly opting in via a
// `static constexpr bool is_reliable_transport_test_double = true;` declaration.
// The opt-in exists ONLY for unit-test doubles that simulate BufferedSender's
// retry/error-queue contract in memory, with no real transport at all (see
// e.g. FakeClient in buffered_sender_smoke_test.cpp) -- forcing those to
// inherit real socket/heartbeat/reader-loop machinery just to satisfy this
// concept would be exactly the kind of unneeded-capability cost this
// project's own economic stance argues against. The declaration must be
// explicit and visible at the double's own definition -- never silently
// inferred -- so a real, non-reliable client (a plain UDPClient, say) can
// never slip through by accident; someone would have to deliberately lie
// about it.
template <typename T>
concept MultiplexedClient =
    decltype(is_multiplexed_stream_client(std::declval<T*>()))::value ||
    requires { requires T::is_reliable_transport_test_double; };
