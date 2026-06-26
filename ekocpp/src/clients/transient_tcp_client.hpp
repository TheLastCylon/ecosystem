#pragma once

#include <string>

#include "stream_client_base.hpp"

// Mirrors ekosis/clients/transient_tcp.py's TransientTCPClient.
class TransientTCPClient : public StreamClientBase<asio::ip::tcp::socket> {
public:
    TransientTCPClient(
        asio::any_io_executor     executor,
        std::string               server_host,
        uint16_t                  server_port,
        std::chrono::milliseconds timeout     = std::chrono::seconds{5},
        int                       max_retries = 3,
        std::chrono::milliseconds retry_delay = std::chrono::milliseconds{100}
    );

protected:
    asio::awaitable<asio::ip::tcp::socket> open_connection() override;

private:
    asio::any_io_executor executor_;
    std::string           host_;
    uint16_t              port_;
};
