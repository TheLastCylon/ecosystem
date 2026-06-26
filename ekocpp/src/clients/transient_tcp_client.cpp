#include "transient_tcp_client.hpp"

TransientTCPClient::TransientTCPClient(
    asio::any_io_executor executor, std::string server_host, uint16_t server_port,
    std::chrono::milliseconds timeout, int max_retries, std::chrono::milliseconds retry_delay
) : StreamClientBase<asio::ip::tcp::socket>(timeout, max_retries, retry_delay),
    executor_(executor),
    host_(std::move(server_host)),
    port_(server_port) {}

asio::awaitable<asio::ip::tcp::socket> TransientTCPClient::open_connection() {
    asio::ip::tcp::socket socket(executor_);
    co_await socket.async_connect(
        asio::ip::tcp::endpoint(asio::ip::make_address(host_), port_), asio::use_awaitable
    );
    co_return socket;
}
