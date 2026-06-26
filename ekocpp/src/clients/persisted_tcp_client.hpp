#pragma once

#include <string>

#include "persistent_stream_client_base.hpp"

// Mirrors ekosis/clients/persisted_tcp.py's PersistedTCPClient. Must be
// constructed via std::make_shared -- see PersistentStreamClientBase for why
// (the heartbeat coroutine needs weak_from_this()). Call start() once after
// construction, and co_await stop() before releasing the last shared_ptr.
class PersistedTCPClient : public PersistentStreamClientBase<asio::ip::tcp::socket> {
public:
    PersistedTCPClient(
        asio::any_io_executor     executor,
        std::string               server_host,
        uint16_t                  server_port,
        std::chrono::milliseconds timeout          = std::chrono::seconds{5},
        std::chrono::milliseconds heartbeat_period = std::chrono::seconds{60},
        int                       max_retries      = 3,
        std::chrono::milliseconds retry_delay      = std::chrono::milliseconds{100}
    );

protected:
    asio::awaitable<asio::ip::tcp::socket> open_connection() override;

private:
    asio::any_io_executor executor_;
    std::string           host_;
    uint16_t              port_;
};
