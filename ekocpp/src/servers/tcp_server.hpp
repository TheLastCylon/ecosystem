#pragma once

#include <asio.hpp>
#include <string>

#include "server_base.hpp"

// Mirrors ekosis/servers/tcp.py's TCPServer. Owns the acceptor lifecycle;
// the actual per-connection framing loop lives in stream_server_base.hpp,
// shared with UDSServer.
class TCPServer : public ServerBase {
public:
    TCPServer(asio::io_context& io_context, RequestRouter& router, std::string host, uint16_t port);

    asio::awaitable<void> serve();
    void                  stop();

private:
    asio::io_context&       io_context_;
    std::string             host_;
    uint16_t                port_;
    asio::ip::tcp::acceptor acceptor_;
};
