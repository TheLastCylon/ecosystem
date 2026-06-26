#pragma once

#include <atomic>
#include <chrono>
#include <memory>
#include <optional>

#include <asio/experimental/channel.hpp>

#include "client_base.hpp"

template <typename SocketType> class PersistentStreamClientBase;

// Defined in persistent_stream_client_base.cpp. Forward-declared here so it
// can be named in the friend declaration below -- see that declaration's
// comment for why this has to be a free function rather than a member.
template <typename SocketType>
asio::awaitable<void> run_heartbeat_loop(std::weak_ptr<PersistentStreamClientBase<SocketType>> weak_self);

// Mirrors ekosis/clients/persistent_stream_client_base.py's
// PersistentStreamClientBase -- keeps one connection open across calls
// instead of opening/closing per message, and runs a background heartbeat
// coroutine to detect a stale connection between real sends.
//
// Must be held via std::shared_ptr (enable_shared_from_this) -- the
// heartbeat coroutine outlives any single send_message() call and captures
// a weak_ptr to self rather than `this`, so a destroyed client is never
// dereferenced, only fails to lock(). stop() must be co_awaited before
// letting the last shared_ptr go, to deterministically confirm the
// heartbeat loop has actually exited (not just been asked to) -- see
// heartbeat_done_ below.
template <typename SocketType>
class PersistentStreamClientBase : public ClientBase,
                                    public std::enable_shared_from_this<PersistentStreamClientBase<SocketType>> {
public:
    explicit PersistentStreamClientBase(
        asio::any_io_executor     executor,
        std::chrono::milliseconds timeout          = std::chrono::seconds{5},
        std::chrono::milliseconds heartbeat_period = std::chrono::seconds{60},
        int                       max_retries      = 3,
        std::chrono::milliseconds retry_delay      = std::chrono::milliseconds{100}
    );

    // Call once, after construction, to start the background heartbeat.
    // Not done in the constructor -- shared_from_this()/weak_from_this()
    // are unsafe to call before the object is fully owned by a shared_ptr.
    void start();

    // Co_await before releasing the last shared_ptr to this client, to
    // confirm the heartbeat loop has actually exited before teardown.
    asio::awaitable<void> stop();

protected:
    virtual asio::awaitable<SocketType> open_connection() = 0;

    asio::awaitable<std::vector<uint8_t>> send_message_retry_loop(std::vector<uint8_t> request) override;

private:
    // Deliberately NOT member functions invoked as part of the long-lived
    // heartbeat loop -- a member-function coroutine's frame always stores an
    // implicit `this`, which would dangle the moment this object is
    // destroyed, regardless of any weak_ptr discipline used inside the body.
    // The free function in persistent_stream_client_base.cpp takes a
    // std::weak_ptr by value instead, and only ever calls into this object
    // through a freshly re-locked shared_ptr, one loop iteration at a time.
    friend asio::awaitable<void> run_heartbeat_loop<SocketType>(std::weak_ptr<PersistentStreamClientBase<SocketType>> weak_self);

    asio::awaitable<void> do_heartbeat();
    asio::awaitable<void> ensure_connected();

    asio::any_io_executor     executor_;
    std::chrono::milliseconds timeout_;
    std::chrono::milliseconds heartbeat_period_;
    std::atomic<bool>         stopping_{false};
    bool                      connected_ = false;
    std::optional<SocketType> socket_;
    asio::steady_timer        heartbeat_timer_;
    asio::experimental::channel<void(std::error_code)> heartbeat_done_;
};
