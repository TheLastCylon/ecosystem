#include "persisted_uds_client.hpp"

PersistedUDSClient::PersistedUDSClient(
    asio::any_io_executor executor, std::string socket_path,
    std::chrono::milliseconds timeout, std::chrono::milliseconds heartbeat_period,
    int max_retries, std::chrono::milliseconds retry_delay
) : PersistentStreamClientBase<asio::local::stream_protocol::socket>(executor, timeout, heartbeat_period, max_retries, retry_delay),
    executor_(executor),
    socket_path_(std::move(socket_path)) {}

asio::awaitable<asio::local::stream_protocol::socket> PersistedUDSClient::open_connection() {
    asio::local::stream_protocol::socket socket(executor_);
    co_await socket.async_connect(asio::local::stream_protocol::endpoint(socket_path_), asio::use_awaitable);
    co_return socket;
}
