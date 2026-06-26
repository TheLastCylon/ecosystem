#include "transient_uds_client.hpp"

TransientUDSClient::TransientUDSClient(
    asio::any_io_executor executor, std::string socket_path,
    std::chrono::milliseconds timeout, int max_retries, std::chrono::milliseconds retry_delay
) : StreamClientBase<asio::local::stream_protocol::socket>(timeout, max_retries, retry_delay),
    executor_(executor),
    socket_path_(std::move(socket_path)) {}

asio::awaitable<asio::local::stream_protocol::socket> TransientUDSClient::open_connection() {
    asio::local::stream_protocol::socket socket(executor_);
    co_await socket.async_connect(asio::local::stream_protocol::endpoint(socket_path_), asio::use_awaitable);
    co_return socket;
}
