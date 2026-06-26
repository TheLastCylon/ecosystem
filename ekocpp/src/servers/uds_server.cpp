#include "uds_server.hpp"

#include <unistd.h>

#include "stream_server_base.hpp"

UDSServer::UDSServer(asio::io_context& io_context, RequestRouter& router, std::string socket_path)
    : ServerBase(router),
      io_context_(io_context),
      socket_path_(std::move(socket_path)),
      acceptor_(io_context_) {
    set_transport_type("UDS");

    // A stale socket file left behind by a previous crashed run blocks bind()
    // with EADDRINUSE -- unlink it first, ignoring "doesn't exist" (the common case).
    ::unlink(socket_path_.c_str());

    asio::local::stream_protocol::endpoint endpoint(socket_path_);
    acceptor_.open(endpoint.protocol());
    acceptor_.bind(endpoint);
    acceptor_.listen();
}

asio::awaitable<void> UDSServer::serve() {
    running_ = true;
    for (;;) {
        auto socket = co_await acceptor_.async_accept(asio::use_awaitable);
        asio::co_spawn(io_context_, handle_stream_connection(std::move(socket), static_cast<ServerBase&>(*this)), asio::detached);
    }
}

void UDSServer::stop() {
    running_ = false;
    acceptor_.close();
    ::unlink(socket_path_.c_str());
}
