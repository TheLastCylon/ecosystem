#pragma once

#include <asio.hpp>

#include "server_base.hpp"

// Mirrors ekosis/servers/stream_server_base.py's StreamServerBase -- the
// framing loop shared by TCP and UDS (both are asio stream sockets; UDP is
// datagram-bounded and has its own loop in udp_server.hpp).
//
// Templated on SocketType rather than asio::ip::tcp::socket directly, since
// asio::local::stream_protocol::socket supports the exact same
// async_read/async_write calls but is a distinct concrete type. Explicit
// instantiations live in tcp_server.cpp/uds_server.cpp -- this loop's body
// is written once, here, regardless of transport.
//
// Per-connection loop: read the fixed 32B header, answer PING_FLAG frames
// directly (never reaching ServerBase::route_request), read the rest of the
// frame, msgpack-unpack the body, route, write the response frame, repeat
// until the connection drops.
template <typename SocketType>
asio::awaitable<void> handle_stream_connection(SocketType socket, ServerBase& server);
