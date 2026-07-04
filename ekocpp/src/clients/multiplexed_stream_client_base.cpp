#include "multiplexed_stream_client_base.hpp"

#include <array>

#include <asio/experimental/awaitable_operators.hpp>
#include <spdlog/spdlog.h>

#include "../data_transfer_objects/binary_frame.hpp"
#include "../exceptions/exceptions.hpp"

using namespace asio::experimental::awaitable_operators;

template <typename SocketType>
MultiplexedStreamClientBase<SocketType>::MultiplexedStreamClientBase(
    asio::any_io_executor executor, std::chrono::milliseconds timeout, std::chrono::milliseconds heartbeat_period,
    int max_retries, std::chrono::milliseconds retry_delay,
    std::chrono::milliseconds staleness_sweep_period, std::chrono::milliseconds staleness_warning_threshold
) : ClientBase(max_retries, retry_delay),
    executor_(executor),
    timeout_(timeout),
    heartbeat_period_(heartbeat_period),
    staleness_sweep_period_(staleness_sweep_period),
    staleness_warning_threshold_(staleness_warning_threshold),
    heartbeat_timer_(executor_),
    staleness_sweep_timer_(executor_),
    heartbeat_done_(executor_, 1),
    staleness_sweep_done_(executor_, 1),
    write_permit_(executor_, 1),
    connect_permit_(executor_, 1) {
    write_permit_.try_send(std::error_code{});   // one permit available immediately
    connect_permit_.try_send(std::error_code{}); // one permit available immediately
}

template <typename SocketType>
void MultiplexedStreamClientBase<SocketType>::start() {
    asio::co_spawn(executor_, run_heartbeat_loop<SocketType>(this->weak_from_this()), asio::detached);
    asio::co_spawn(executor_, run_staleness_sweep_loop<SocketType>(this->weak_from_this()), asio::detached);
}

template <typename SocketType>
asio::awaitable<void> MultiplexedStreamClientBase<SocketType>::stop() {
    stopping_.store(true);
    heartbeat_timer_.cancel();       // wakes both loops immediately instead of waiting out their periods
    staleness_sweep_timer_.cancel();
    co_await heartbeat_done_.async_receive(asio::use_awaitable);
    co_await staleness_sweep_done_.async_receive(asio::use_awaitable);
}

template <typename SocketType>
asio::awaitable<void> MultiplexedStreamClientBase<SocketType>::ensure_connected() {
    co_await connect_permit_.async_receive(asio::use_awaitable);
    struct PermitGuard {
        asio::experimental::concurrent_channel<void(std::error_code)>& permit;
        ~PermitGuard() { permit.try_send(std::error_code{}); }
    } guard{connect_permit_};

    if (!connected_) {
        socket_    = co_await open_connection();
        connected_ = true;
        asio::co_spawn(executor_, run_reader_loop<SocketType>(this->weak_from_this()), asio::detached);
    }
}

template <typename SocketType>
void MultiplexedStreamClientBase<SocketType>::fail_all_outstanding(std::error_code ec) {
    std::lock_guard<std::mutex> lock(demux_mutex_);
    for (auto& [key, entry] : demux_map_) {
        entry.channel->try_send(ec, std::vector<uint8_t>{});
    }
    demux_map_.clear();
}

// Mirrors PersistentStreamClientBase::do_heartbeat's intent (a bare ping/pong
// round trip, answered by the server's transport layer alone, never reaching
// its router) but rides the same demux as every other caller -- it cannot
// perform its own independent async_read the way the Persisted version does,
// since the reader loop is now the socket's sole reader. See
// multiplexed_stream_client.md's "Reconnection" section for why this is
// forced correctness, not a style choice.
template <typename SocketType>
asio::awaitable<void> MultiplexedStreamClientBase<SocketType>::do_heartbeat() {
    try {
        co_await ensure_connected();
    } catch (const std::system_error&) {
        co_return; // connection refused
    }

    const SpanKey                 ping_key = SpanKey::generate();
    auto                          channel  = std::make_shared<DemuxChannel>(executor_, 1);
    {
        std::lock_guard<std::mutex> lock(demux_mutex_);
        demux_map_[ping_key] = DemuxEntry{channel, std::chrono::steady_clock::now(), false};
    }

    try {
        const auto ping = pack_ping_frame(ping_key);

        co_await write_permit_.async_receive(asio::use_awaitable);
        {
            struct PermitGuard {
                asio::experimental::concurrent_channel<void(std::error_code)>& permit;
                ~PermitGuard() { permit.try_send(std::error_code{}); }
            } guard{write_permit_};
            co_await asio::async_write(*socket_, asio::buffer(ping), asio::use_awaitable);
        }

        asio::steady_timer timer(co_await asio::this_coro::executor, timeout_);
        auto result = co_await (
            channel->async_receive(asio::use_awaitable) || timer.async_wait(asio::use_awaitable)
        );

        {
            std::lock_guard<std::mutex> lock(demux_mutex_);
            demux_map_.erase(ping_key);
        }

        if (result.index() == 1) {
            connected_ = false; // timed out waiting for the pong
            co_return;
        }

        // A set error_code on the channel (fail_all_outstanding) is thrown as
        // a std::system_error by use_awaitable, not returned here -- caught
        // below, same as any other write/read failure.
        const auto& pong_frame = std::get<0>(result);
        if (pong_frame.size() < HEADER_LENGTH) {
            connected_ = false;
            co_return;
        }
        const ParsedHeader parsed = parse_header(pong_frame.data());
        if (!(parsed.flags & PING_FLAG)) {
            connected_ = false;
        }
    } catch (const std::system_error&) {
        connected_ = false;
    }
}

template <typename SocketType>
asio::awaitable<std::vector<uint8_t>> MultiplexedStreamClientBase<SocketType>::send_message_retry_loop(std::vector<uint8_t> request) {
    // co_await is not permitted inside a catch block -- the executor is
    // fetched once up front; see the matching comment in
    // persistent_stream_client_base.cpp.
    auto executor = co_await asio::this_coro::executor;

    const SpanKey span_key = parse_header(request.data()).span_key;
    int           retry_count = 0;

    while (retry_count < max_retries_) {
        bool should_retry = false;
        auto channel       = std::make_shared<DemuxChannel>(executor, 1);
        try {
            co_await ensure_connected();

            {
                std::lock_guard<std::mutex> lock(demux_mutex_);
                demux_map_[span_key] = DemuxEntry{channel, std::chrono::steady_clock::now(), false};
            }

            co_await write_permit_.async_receive(asio::use_awaitable);
            {
                struct PermitGuard {
                    asio::experimental::concurrent_channel<void(std::error_code)>& permit;
                    ~PermitGuard() { permit.try_send(std::error_code{}); }
                } guard{write_permit_};
                co_await asio::async_write(*socket_, asio::buffer(request), asio::use_awaitable);
            }

            // Deliberately NOT raced against a timer -- an ordinary send has
            // no per-request timeout. See multiplexed_stream_client.md's
            // "Per-request timeout" section: multiplexing means a slow
            // response no longer blocks anything else, and connection death
            // is already handled below via fail_all_outstanding. A
            // permanently-unanswered entry is a staleness-sweep warning, not
            // a retry trigger.
            //
            // A set error_code on the channel (fail_all_outstanding) is
            // thrown as a std::system_error by use_awaitable here, not
            // returned -- caught below, same as a failed write.
            std::vector<uint8_t> response_frame = co_await channel->async_receive(asio::use_awaitable);

            {
                std::lock_guard<std::mutex> lock(demux_mutex_);
                demux_map_.erase(span_key);
            }

            co_return response_frame;
        } catch (const std::system_error&) {
            {
                std::lock_guard<std::mutex> lock(demux_mutex_);
                demux_map_.erase(span_key);
            }
            connected_   = false;
            should_retry = true;
        }

        if (should_retry) {
            ++retry_count;
            if (retry_count >= max_retries_) {
                throw CommunicationsMaxRetriesReached("Maximum retries exceeded in sending request.");
            }
            asio::steady_timer retry_timer(executor, retry_delay_);
            co_await retry_timer.async_wait(asio::use_awaitable);
        }
    }
    throw CommunicationsMaxRetriesReached("Maximum retries exceeded in sending request.");
}

// Free function -- see the forward declaration's comment for why. Sole
// reader of the socket it's bound to (spawned fresh by ensure_connected()
// each time it reconnects -- see multiplexed_stream_client.md's
// "Reconnection" section for why one long-lived loop surviving reconnects
// was rejected in favour of this).
template <typename SocketType>
asio::awaitable<void> run_reader_loop(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self) {
    for (;;) {
        auto self = weak_self.lock();
        if (!self) co_return; // owner is gone -- nothing left to read for.

        try {
            std::array<uint8_t, HEADER_LENGTH> header{};
            co_await asio::async_read(*self->socket_, asio::buffer(header), asio::use_awaitable);
            const ParsedHeader parsed = parse_header(header.data());

            std::vector<uint8_t> rest(parsed.total_len);
            if (parsed.total_len > 0) {
                co_await asio::async_read(*self->socket_, asio::buffer(rest), asio::use_awaitable);
            }

            std::vector<uint8_t> frame;
            frame.reserve(HEADER_LENGTH + rest.size());
            frame.insert(frame.end(), header.begin(), header.end());
            frame.insert(frame.end(), rest.begin(), rest.end());

            std::shared_ptr<typename MultiplexedStreamClientBase<SocketType>::DemuxChannel> channel;
            {
                std::lock_guard<std::mutex> lock(self->demux_mutex_);
                auto it = self->demux_map_.find(parsed.span_key);
                if (it != self->demux_map_.end()) {
                    channel = it->second.channel;
                    self->demux_map_.erase(it);
                }
            }
            if (channel) {
                channel->try_send(std::error_code{}, std::move(frame));
            }
            // else: orphan response (already timed out / stale) -- discarded.
        } catch (const std::system_error& e) {
            self->fail_all_outstanding(e.code());
            self->connected_ = false;
            co_return; // this loop's connection is dead -- the next ensure_connected() spawns a fresh one.
        }
    }
}

// Free function -- same lifetime discipline as PersistentStreamClientBase's
// run_heartbeat_loop.
template <typename SocketType>
asio::awaitable<void> run_heartbeat_loop(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self) {
    for (;;) {
        auto self = weak_self.lock();
        if (!self) co_return;

        self->heartbeat_timer_.expires_after(self->heartbeat_period_);
        try {
            co_await self->heartbeat_timer_.async_wait(asio::use_awaitable);
        } catch (const std::system_error&) {
            break; // cancelled by stop() (or the timer's own destructor, if the owner forgot to call stop())
        }

        if (self->stopping_.load()) break;

        co_await self->do_heartbeat();
    }

    if (auto self = weak_self.lock()) {
        self->heartbeat_done_.try_send(std::error_code{});
    }
}

// Free function -- periodic sweep, structurally mirroring run_heartbeat_loop.
// Never removes entries, never retries, never touches the connection --
// purely operational visibility. See multiplexed_stream_client.md's
// "Per-request timeout" section.
template <typename SocketType>
asio::awaitable<void> run_staleness_sweep_loop(std::weak_ptr<MultiplexedStreamClientBase<SocketType>> weak_self) {
    for (;;) {
        auto self = weak_self.lock();
        if (!self) co_return;

        self->staleness_sweep_timer_.expires_after(self->staleness_sweep_period_);
        try {
            co_await self->staleness_sweep_timer_.async_wait(asio::use_awaitable);
        } catch (const std::system_error&) {
            break;
        }

        if (self->stopping_.load()) break;

        {
            std::lock_guard<std::mutex> lock(self->demux_mutex_);
            const auto now = std::chrono::steady_clock::now();
            for (auto& [key, entry] : self->demux_map_) {
                if (!entry.warned && (now - entry.registered_at) >= self->staleness_warning_threshold_) {
                    entry.warned = true;
                    spdlog::warn(
                        "MultiplexedStreamClientBase: request with span_key {} has been unanswered for over {}ms -- "
                        "connection is healthy, so this is likely a server-side bug that never wrote a response. "
                        "Not auto-retried; needs manual investigation.",
                        key.to_string(), self->staleness_warning_threshold_.count()
                    );
                }
            }
        }
    }

    if (auto self = weak_self.lock()) {
        self->staleness_sweep_done_.try_send(std::error_code{});
    }
}

template class MultiplexedStreamClientBase<asio::ip::tcp::socket>;
template class MultiplexedStreamClientBase<asio::local::stream_protocol::socket>;

template asio::awaitable<void> run_heartbeat_loop<asio::ip::tcp::socket>(
    std::weak_ptr<MultiplexedStreamClientBase<asio::ip::tcp::socket>>);
template asio::awaitable<void> run_heartbeat_loop<asio::local::stream_protocol::socket>(
    std::weak_ptr<MultiplexedStreamClientBase<asio::local::stream_protocol::socket>>);

template asio::awaitable<void> run_reader_loop<asio::ip::tcp::socket>(
    std::weak_ptr<MultiplexedStreamClientBase<asio::ip::tcp::socket>>);
template asio::awaitable<void> run_reader_loop<asio::local::stream_protocol::socket>(
    std::weak_ptr<MultiplexedStreamClientBase<asio::local::stream_protocol::socket>>);

template asio::awaitable<void> run_staleness_sweep_loop<asio::ip::tcp::socket>(
    std::weak_ptr<MultiplexedStreamClientBase<asio::ip::tcp::socket>>);
template asio::awaitable<void> run_staleness_sweep_loop<asio::local::stream_protocol::socket>(
    std::weak_ptr<MultiplexedStreamClientBase<asio::local::stream_protocol::socket>>);
