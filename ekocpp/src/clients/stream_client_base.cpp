#include "stream_client_base.hpp"

#include <array>

#include <asio/experimental/awaitable_operators.hpp>

#include "../data_transfer_objects/binary_frame.hpp"
#include "../exceptions/exceptions.hpp"

using namespace asio::experimental::awaitable_operators;

template <typename SocketType>
StreamClientBase<SocketType>::StreamClientBase(std::chrono::milliseconds timeout, int max_retries, std::chrono::milliseconds retry_delay)
    : ClientBase(max_retries, retry_delay), timeout_(timeout) {}

template <typename SocketType>
asio::awaitable<std::vector<uint8_t>> StreamClientBase<SocketType>::send_message_once(const std::vector<uint8_t>& request) {
    SocketType socket = co_await open_connection();
    co_await asio::async_write(socket, asio::buffer(request), asio::use_awaitable);

    asio::steady_timer timer(co_await asio::this_coro::executor);

    std::array<uint8_t, HEADER_LENGTH> header{};
    timer.expires_after(timeout_);
    auto header_result = co_await (
        asio::async_read(socket, asio::buffer(header), asio::use_awaitable) || timer.async_wait(asio::use_awaitable)
    );
    if (header_result.index() == 1) {
        throw CommunicationsEmptyResponse("Timed out waiting for response header.");
    }

    const ParsedHeader parsed = parse_header(header.data());

    std::vector<uint8_t> rest(parsed.total_len);
    if (parsed.total_len > 0) {
        timer.expires_after(timeout_);
        auto rest_result = co_await (
            asio::async_read(socket, asio::buffer(rest), asio::use_awaitable) || timer.async_wait(asio::use_awaitable)
        );
        if (rest_result.index() == 1) {
            throw CommunicationsEmptyResponse("Timed out waiting for response body.");
        }
    }

    std::vector<uint8_t> response_frame;
    response_frame.reserve(HEADER_LENGTH + rest.size());
    response_frame.insert(response_frame.end(), header.begin(), header.end());
    response_frame.insert(response_frame.end(), rest.begin(), rest.end());

    co_return response_frame;
}

// Mirrors StreamClientBase._send_message_retry_loop's retryable/non-retryable
// split, minus the persistent-connection-specific reconnect logic (transient
// clients open a fresh connection every call -- there's no stale connection
// state to recover from, just a failed attempt to retry).
template <typename SocketType>
asio::awaitable<std::vector<uint8_t>> StreamClientBase<SocketType>::send_message_retry_loop(std::vector<uint8_t> request) {
    // co_await is not permitted inside a catch block (a genuine C++20
    // coroutine restriction -- suspending while exception-handling machinery
    // is active isn't well-defined) -- the executor is fetched once up front,
    // and the catch blocks only set a flag; the actual retry delay co_await
    // happens after the catch, once the handler has already exited.
    auto executor = co_await asio::this_coro::executor;

    while (retry_count_ < max_retries_ && !success_) {
        bool should_retry = false;
        try {
            auto response = co_await send_message_once(request);
            success_ = true;
            co_return response;
        } catch (const std::system_error&) {
            // Connection refused/reset/timeout -- retryable, same family Python
            // catches as (TimeoutError, ConnectionResetError, ConnectionAbortedError, BrokenPipeError).
            should_retry = true;
        } catch (const CommunicationsEmptyResponse&) {
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

template class StreamClientBase<asio::ip::tcp::socket>;
template class StreamClientBase<asio::local::stream_protocol::socket>;
