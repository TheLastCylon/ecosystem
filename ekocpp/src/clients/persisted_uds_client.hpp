#pragma once

#include <string>

#include "persistent_stream_client_base.hpp"

// Mirrors ekosis/clients/persisted_uds.py's PersistedUDSClient. Same
// shared_ptr/start()/stop() lifecycle requirement as PersistedTCPClient --
// see PersistentStreamClientBase.
class PersistedUDSClient : public PersistentStreamClientBase<asio::local::stream_protocol::socket> {
public:
    PersistedUDSClient(
        asio::any_io_executor     executor,
        std::string               socket_path,
        std::chrono::milliseconds timeout          = std::chrono::seconds{5},
        std::chrono::milliseconds heartbeat_period = std::chrono::seconds{60},
        int                       max_retries      = 3,
        std::chrono::milliseconds retry_delay      = std::chrono::milliseconds{100}
    );

protected:
    asio::awaitable<asio::local::stream_protocol::socket> open_connection() override;

private:
    asio::any_io_executor executor_;
    std::string           socket_path_;
};
