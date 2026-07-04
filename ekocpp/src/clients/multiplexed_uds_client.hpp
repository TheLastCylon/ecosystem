#pragma once

#include <string>

#include "multiplexed_stream_client_base.hpp"

// Mirrors PersistedUDSClient's shape -- see multiplexed_stream_client.md for
// the full design. Same shared_ptr/start()/stop() lifecycle requirement as
// MultiplexedTCPClient -- see MultiplexedStreamClientBase.
class MultiplexedUDSClient : public MultiplexedStreamClientBase<asio::local::stream_protocol::socket> {
public:
    MultiplexedUDSClient(
        asio::any_io_executor     executor,
        std::string               socket_path,
        std::chrono::milliseconds timeout                   = std::chrono::seconds{5},
        std::chrono::milliseconds heartbeat_period           = std::chrono::seconds{60},
        int                       max_retries                = 3,
        std::chrono::milliseconds retry_delay                = std::chrono::milliseconds{100},
        std::chrono::milliseconds staleness_sweep_period      = std::chrono::seconds{30},
        std::chrono::milliseconds staleness_warning_threshold = std::chrono::seconds{60}
    );

protected:
    asio::awaitable<asio::local::stream_protocol::socket> open_connection() override;

private:
    asio::any_io_executor executor_;
    std::string           socket_path_;
};
