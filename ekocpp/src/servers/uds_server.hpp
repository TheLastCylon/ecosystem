#pragma once

#include <asio.hpp>
#include <string>

#include "server_base.hpp"

// Mirrors ekosis/servers/uds.py's UDSServer. Same acceptor-lifecycle shape
// as TCPServer; shares the stream_server_base.hpp framing loop, templated
// over asio::local::stream_protocol::socket here instead of tcp::socket.
//
// Unlike the Python side (which checks hasattr(socket, "AF_UNIX") since
// Windows lacks it), UDS support is a compile-time guarantee on Linux --
// no runtime "not supported on this platform" branch needed for the
// Linux-only targets ekocpp currently builds for.
class UDSServer : public ServerBase {
public:
    UDSServer(asio::io_context& io_context, RequestRouter& router, std::string socket_path);

    asio::awaitable<void> serve();
    void                  stop();

private:
    asio::io_context&                  io_context_;
    std::string                        socket_path_;
    asio::local::stream_protocol::acceptor acceptor_;
};
