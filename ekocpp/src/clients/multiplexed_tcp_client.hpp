#pragma once

#include <string>

#include "multiplexed_stream_client_base.hpp"

// Mirrors PersistedTCPClient's shape -- see multiplexed_stream_client.md for
// the full design. Must be constructed via std::make_shared -- see
// MultiplexedStreamClientBase for why. Call start() once after construction,
// and co_await stop() before releasing the last shared_ptr.
class MultiplexedTCPClient : public MultiplexedStreamClientBase<asio::ip::tcp::socket> {
public:
    MultiplexedTCPClient(
        asio::any_io_executor     executor,
        std::string               server_host,
        uint16_t                  server_port,
        std::chrono::milliseconds timeout                   = std::chrono::seconds{5},
        std::chrono::milliseconds heartbeat_period           = std::chrono::seconds{60},
        int                       max_retries                = 3,
        std::chrono::milliseconds retry_delay                = std::chrono::milliseconds{100},
        std::chrono::milliseconds staleness_sweep_period      = std::chrono::seconds{30},
        std::chrono::milliseconds staleness_warning_threshold = std::chrono::seconds{60}
    );

protected:
    asio::awaitable<asio::ip::tcp::socket> open_connection() override;

private:
    asio::any_io_executor executor_;
    std::string           host_;
    uint16_t              port_;
};
