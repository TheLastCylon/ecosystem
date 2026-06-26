#pragma once

#include <asio.hpp>
#include <array>
#include <string>

#include "server_base.hpp"

// Mirrors ekosis/servers/udp.py's UDPServer/DatagramProtocolServer. Separate
// from stream_server_base.hpp -- a UDP datagram is already whole in memory
// on arrival, so there's no incremental header-then-rest read, just a slice
// of the fixed 32B header off the front of whatever async_receive_from returned.
class UDPServer : public ServerBase {
public:
    UDPServer(asio::io_context& io_context, RequestRouter& router, std::string host, uint16_t port);

    asio::awaitable<void> serve();
    void                  stop();

private:
    asio::awaitable<void> receive_loop();

    asio::io_context&    io_context_;
    std::string          host_;
    uint16_t             port_;
    asio::ip::udp::socket socket_;
};
