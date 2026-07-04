#include "multiplexed_tcp_client.hpp"

MultiplexedTCPClient::MultiplexedTCPClient(
    asio::any_io_executor executor, std::string server_host, uint16_t server_port,
    std::chrono::milliseconds timeout, std::chrono::milliseconds heartbeat_period,
    int max_retries, std::chrono::milliseconds retry_delay,
    std::chrono::milliseconds staleness_sweep_period, std::chrono::milliseconds staleness_warning_threshold
) : MultiplexedStreamClientBase<asio::ip::tcp::socket>(
        executor, timeout, heartbeat_period, max_retries, retry_delay,
        staleness_sweep_period, staleness_warning_threshold
    ),
    executor_(executor),
    host_(std::move(server_host)),
    port_(server_port) {}

asio::awaitable<asio::ip::tcp::socket> MultiplexedTCPClient::open_connection() {
    asio::ip::tcp::socket socket(executor_);
    co_await socket.async_connect(
        asio::ip::tcp::endpoint(asio::ip::make_address(host_), port_), asio::use_awaitable
    );
    co_return socket;
}
