#include "persisted_tcp_client.hpp"

PersistedTCPClient::PersistedTCPClient(
    asio::any_io_executor executor, std::string server_host, uint16_t server_port,
    std::chrono::milliseconds timeout, std::chrono::milliseconds heartbeat_period,
    int max_retries, std::chrono::milliseconds retry_delay
) : PersistentStreamClientBase<asio::ip::tcp::socket>(executor, timeout, heartbeat_period, max_retries, retry_delay),
    executor_(executor),
    host_(std::move(server_host)),
    port_(server_port) {}

asio::awaitable<asio::ip::tcp::socket> PersistedTCPClient::open_connection() {
    asio::ip::tcp::socket socket(executor_);
    co_await socket.async_connect(
        asio::ip::tcp::endpoint(asio::ip::make_address(host_), port_), asio::use_awaitable
    );
    co_return socket;
}
