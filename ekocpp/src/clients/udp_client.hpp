#pragma once

#include <chrono>
#include <optional>
#include <string>

#include <asio.hpp>
#include <asio/experimental/channel.hpp>

#include "client_base.hpp"

// Mirrors ekosis/clients/{datagram_client_base,udp}.py collapsed into one
// class -- Python splits DatagramClientBase/UDPClient, but UDPClient adds
// nothing over its base (no second datagram transport exists to share the
// base with), so there's no reason to keep two C++ classes for one concrete
// thing. Lazily opens its UDP socket on first send and keeps it open across
// calls (UDP has no "connection" to persist, but the transport/socket itself
// is reused, same as the Python side).
class UDPClient : public ClientBase {
public:
    UDPClient(
        asio::any_io_executor     executor,
        std::string               server_host,
        uint16_t                  server_port,
        std::chrono::milliseconds timeout     = std::chrono::seconds{5},
        int                       max_retries = 3,
        std::chrono::milliseconds retry_delay = std::chrono::milliseconds{100}
    );

protected:
    asio::awaitable<std::vector<uint8_t>> send_message_retry_loop(std::vector<uint8_t> request) override;

private:
    asio::awaitable<void>                 ensure_initialised();
    asio::awaitable<std::vector<uint8_t>> send_once(const std::vector<uint8_t>& request);

    asio::any_io_executor                executor_;
    std::string                          host_;
    uint16_t                             port_;
    std::chrono::milliseconds            timeout_;
    bool                                 initialised_ = false;
    std::optional<asio::ip::udp::socket> socket_;

    // Single-slot semaphore (acquire = receive, release = send into it) --
    // serializes concurrent send_message() calls onto the one shared socket,
    // same role Python's asyncio.Lock plays in DatagramProtocolClient.
    asio::experimental::channel<void(std::error_code)> send_permit_;
};
