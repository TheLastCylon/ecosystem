#include "persistent_stream_client_base.hpp"

#include <array>

#include <asio/experimental/awaitable_operators.hpp>

#include "../data_transfer_objects/binary_frame.hpp"
#include "../exceptions/exceptions.hpp"

using namespace asio::experimental::awaitable_operators;

template <typename SocketType>
PersistentStreamClientBase<SocketType>::PersistentStreamClientBase(
    asio::any_io_executor executor, std::chrono::milliseconds timeout, std::chrono::milliseconds heartbeat_period,
    int max_retries, std::chrono::milliseconds retry_delay
) : ClientBase(max_retries, retry_delay),
    executor_(executor),
    timeout_(timeout),
    heartbeat_period_(heartbeat_period),
    heartbeat_timer_(executor_),
    heartbeat_done_(executor_, 1) {}

template <typename SocketType>
void PersistentStreamClientBase<SocketType>::start() {
    asio::co_spawn(executor_, run_heartbeat_loop<SocketType>(this->weak_from_this()), asio::detached);
}

template <typename SocketType>
asio::awaitable<void> PersistentStreamClientBase<SocketType>::stop() {
    stopping_.store(true);
    heartbeat_timer_.cancel(); // wakes the loop immediately instead of waiting out the period
    co_await heartbeat_done_.async_receive(asio::use_awaitable);
}

template <typename SocketType>
asio::awaitable<void> PersistentStreamClientBase<SocketType>::ensure_connected() {
    if (!connected_) {
        socket_    = co_await open_connection();
        connected_ = true;
    }
}

// Mirrors PersistentStreamClientBase.__do_heartbeat -- a bare 32-byte
// ping/pong round trip, answered by the server's transport layer alone,
// never reaching its router.
template <typename SocketType>
asio::awaitable<void> PersistentStreamClientBase<SocketType>::do_heartbeat() {
    try {
        co_await ensure_connected();
    } catch (const std::system_error&) {
        co_return; // connection refused -- same as Python's bare `return` on ConnectionRefusedError
    }

    try {
        const auto ping = pack_ping_frame(SpanKey::generate());
        co_await asio::async_write(*socket_, asio::buffer(ping), asio::use_awaitable);

        std::array<uint8_t, HEADER_LENGTH> pong{};
        asio::steady_timer timer(co_await asio::this_coro::executor, timeout_);
        auto result = co_await (
            asio::async_read(*socket_, asio::buffer(pong), asio::use_awaitable) || timer.async_wait(asio::use_awaitable)
        );
        if (result.index() == 1) {
            connected_ = false; // timed out waiting for the pong
            co_return;
        }

        const ParsedHeader parsed = parse_header(pong.data());
        if (!(parsed.flags & PING_FLAG)) {
            connected_ = false;
        }
    } catch (const std::system_error&) {
        connected_ = false;
    }
}

template <typename SocketType>
asio::awaitable<std::vector<uint8_t>> PersistentStreamClientBase<SocketType>::send_message_retry_loop(std::vector<uint8_t> request) {
    // co_await is not permitted inside a catch block -- the executor is
    // fetched once up front; see the matching comment in stream_client_base.cpp.
    auto executor = co_await asio::this_coro::executor;

    while (retry_count_ < max_retries_ && !success_) {
        bool should_retry = false;
        try {
            co_await ensure_connected();
            co_await asio::async_write(*socket_, asio::buffer(request), asio::use_awaitable);

            std::array<uint8_t, HEADER_LENGTH> header{};
            co_await asio::async_read(*socket_, asio::buffer(header), asio::use_awaitable);
            const ParsedHeader parsed = parse_header(header.data());

            std::vector<uint8_t> rest(parsed.total_len);
            if (parsed.total_len > 0) {
                co_await asio::async_read(*socket_, asio::buffer(rest), asio::use_awaitable);
            }

            std::vector<uint8_t> response_frame;
            response_frame.reserve(HEADER_LENGTH + rest.size());
            response_frame.insert(response_frame.end(), header.begin(), header.end());
            response_frame.insert(response_frame.end(), rest.begin(), rest.end());

            success_ = true;
            co_return response_frame;
        } catch (const std::system_error&) {
            // Mirrors Python's reconnect-then-retry branch for
            // ConnectionResetError/ConnectionAbortedError/BrokenPipeError/
            // CommunicationsEmptyResponse -- the connection is broken, not
            // just slow, so the next attempt must reconnect first.
            connected_   = false;
            should_retry = true;
        }

        if (should_retry) {
            ++retry_count_;
            if (retry_count_ >= max_retries_) {
                throw CommunicationsMaxRetriesReached("Maximum retries exceeded in sending request.");
            }
            asio::steady_timer retry_timer(executor, retry_delay_);
            co_await retry_timer.async_wait(asio::use_awaitable);
        }
    }
    throw CommunicationsMaxRetriesReached("Maximum retries exceeded in sending request.");
}

// Free function, not a member -- see the friend declaration's comment in
// persistent_stream_client_base.hpp for why. `self` is re-acquired fresh at
// the top of each iteration and released at the end of it (ordinary scope
// exit) -- the object is kept alive for at most one heartbeat_period at a
// time, never indefinitely, and the lock() at the top of the next iteration
// is the checkpoint where a dropped owner is actually noticed.
template <typename SocketType>
asio::awaitable<void> run_heartbeat_loop(std::weak_ptr<PersistentStreamClientBase<SocketType>> weak_self) {
    for (;;) {
        auto self = weak_self.lock();
        if (!self) co_return; // owner is gone -- nothing left to heartbeat for.

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

template class PersistentStreamClientBase<asio::ip::tcp::socket>;
template class PersistentStreamClientBase<asio::local::stream_protocol::socket>;

template asio::awaitable<void> run_heartbeat_loop<asio::ip::tcp::socket>(
    std::weak_ptr<PersistentStreamClientBase<asio::ip::tcp::socket>>);
template asio::awaitable<void> run_heartbeat_loop<asio::local::stream_protocol::socket>(
    std::weak_ptr<PersistentStreamClientBase<asio::local::stream_protocol::socket>>);
