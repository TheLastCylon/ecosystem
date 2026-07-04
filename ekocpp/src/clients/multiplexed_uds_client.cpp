#include "multiplexed_uds_client.hpp"

MultiplexedUDSClient::MultiplexedUDSClient(
    asio::any_io_executor executor, std::string socket_path,
    std::chrono::milliseconds timeout, std::chrono::milliseconds heartbeat_period,
    int max_retries, std::chrono::milliseconds retry_delay,
    std::chrono::milliseconds staleness_sweep_period, std::chrono::milliseconds staleness_warning_threshold
) : MultiplexedStreamClientBase<asio::local::stream_protocol::socket>(
        executor, timeout, heartbeat_period, max_retries, retry_delay,
        staleness_sweep_period, staleness_warning_threshold
    ),
    executor_(executor),
    socket_path_(std::move(socket_path)) {}

asio::awaitable<asio::local::stream_protocol::socket> MultiplexedUDSClient::open_connection() {
    asio::local::stream_protocol::socket socket(executor_);
    co_await socket.async_connect(asio::local::stream_protocol::endpoint(socket_path_), asio::use_awaitable);
    co_return socket;
}
