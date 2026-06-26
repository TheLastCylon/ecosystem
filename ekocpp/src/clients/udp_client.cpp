#include "udp_client.hpp"

#include <asio/experimental/awaitable_operators.hpp>

#include "../exceptions/exceptions.hpp"

using namespace asio::experimental::awaitable_operators;

namespace {
constexpr size_t MAX_DATAGRAM_SIZE = 65536;
}

UDPClient::UDPClient(
    asio::any_io_executor executor, std::string server_host, uint16_t server_port,
    std::chrono::milliseconds timeout, int max_retries, std::chrono::milliseconds retry_delay
) : ClientBase(max_retries, retry_delay),
    executor_(executor),
    host_(std::move(server_host)),
    port_(server_port),
    timeout_(timeout),
    send_permit_(executor_, 1) {
    send_permit_.try_send(std::error_code{}); // one permit available immediately
}

asio::awaitable<void> UDPClient::ensure_initialised() {
    if (!initialised_) {
        socket_.emplace(executor_, asio::ip::udp::endpoint(asio::ip::udp::v4(), 0));
        // connect() on a UDP socket just fixes the default peer for
        // async_send/async_receive -- no handshake, still connectionless.
        co_await socket_->async_connect(
            asio::ip::udp::endpoint(asio::ip::make_address(host_), port_), asio::use_awaitable
        );
        initialised_ = true;
    }
}

asio::awaitable<std::vector<uint8_t>> UDPClient::send_once(const std::vector<uint8_t>& request) {
    co_await ensure_initialised();
    co_await socket_->async_send(asio::buffer(request), asio::use_awaitable);

    asio::steady_timer    timer(co_await asio::this_coro::executor, timeout_);
    std::vector<uint8_t>  buffer(MAX_DATAGRAM_SIZE);
    auto result = co_await (
        socket_->async_receive(asio::buffer(buffer), asio::use_awaitable) || timer.async_wait(asio::use_awaitable)
    );
    if (result.index() == 1) {
        throw CommunicationsEmptyResponse("Timed out waiting for response.");
    }
    buffer.resize(std::get<0>(result));
    co_return buffer;
}

asio::awaitable<std::vector<uint8_t>> UDPClient::send_message_retry_loop(std::vector<uint8_t> request) {
    // Single-slot channel as a binary semaphore: acquire by receiving the one
    // permit, release by sending it back -- serializes concurrent
    // send_message() calls onto the one shared socket, same role Python's
    // asyncio.Lock plays in DatagramProtocolClient.
    co_await send_permit_.async_receive(asio::use_awaitable);
    struct PermitGuard {
        asio::experimental::channel<void(std::error_code)>& permit;
        ~PermitGuard() { permit.try_send(std::error_code{}); }
    } guard{send_permit_};

    auto executor = co_await asio::this_coro::executor;

    while (retry_count_ < max_retries_) {
        bool should_retry = false;
        try {
            auto response = co_await send_once(request);
            success_ = true;
            co_return response;
        } catch (const std::system_error&) {
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
