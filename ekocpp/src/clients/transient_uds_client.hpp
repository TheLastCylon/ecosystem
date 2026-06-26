#pragma once

#include <string>

#include "stream_client_base.hpp"

// Mirrors ekosis/clients/transient_uds.py's TransientUDSClient. No
// hasattr(socket, "AF_UNIX") platform check needed -- UDS support is a
// compile-time guarantee on the Linux-only targets ekocpp builds for,
// same call already made for UDSServer.
class TransientUDSClient : public StreamClientBase<asio::local::stream_protocol::socket> {
public:
    TransientUDSClient(
        asio::any_io_executor     executor,
        std::string               socket_path,
        std::chrono::milliseconds timeout     = std::chrono::seconds{5},
        int                       max_retries = 3,
        std::chrono::milliseconds retry_delay = std::chrono::milliseconds{100}
    );

protected:
    asio::awaitable<asio::local::stream_protocol::socket> open_connection() override;

private:
    asio::any_io_executor executor_;
    std::string           socket_path_;
};
