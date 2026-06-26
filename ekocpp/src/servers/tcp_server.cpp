#include "tcp_server.hpp"

#include "stream_server_base.hpp"

TCPServer::TCPServer(asio::io_context& io_context, RequestRouter& router, std::string host, uint16_t port)
    : ServerBase(router),
      io_context_(io_context),
      host_(std::move(host)),
      port_(port),
      acceptor_(io_context_, asio::ip::tcp::endpoint(asio::ip::make_address(host_), port_)) {
    set_transport_type("TCP");
}

asio::awaitable<void> TCPServer::serve() {
    running_ = true;
    for (;;) {
        auto socket = co_await acceptor_.async_accept(asio::use_awaitable);
        asio::co_spawn(io_context_, handle_stream_connection(std::move(socket), static_cast<ServerBase&>(*this)), asio::detached);
    }
}

void TCPServer::stop() {
    running_ = false;
    acceptor_.close();
}
