#include "udp_server.hpp"

#include "../data_transfer_objects/binary_frame.hpp"

namespace {

constexpr size_t MAX_DATAGRAM_SIZE = 65536;

asio::awaitable<void> handle_datagram(std::vector<uint8_t> bytes_read, asio::ip::udp::endpoint sender, asio::ip::udp::socket& socket, ServerBase& server) {
    if (bytes_read.size() < HEADER_LENGTH) {
        co_return; // Too short to even hold a header -- not a valid frame, drop it.
    }

    const ParsedHeader parsed = parse_header(bytes_read.data());
    co_await asio::this_coro::set_span_key(parsed.span_key);

    if (parsed.flags & PING_FLAG) {
        const auto pong = pack_ping_frame(parsed.span_key);
        co_await socket.async_send_to(asio::buffer(pong), sender, asio::use_awaitable);
        co_return;
    }

    // total_len is attacker/bug-controlled and not yet checked against what
    // actually arrived -- without this guard, a claim bigger than the real
    // datagram drives the iterator arithmetic below straight past
    // bytes_read.end() (out-of-bounds read), not just an oversized allocation.
    if (parsed.total_len > MAX_FRAME_SIZE || HEADER_LENGTH + parsed.total_len > bytes_read.size()) {
        co_return; // Can't trust this datagram's framing -- drop it, no response (sender may be spoofed).
    }

    std::vector<uint8_t> rest(bytes_read.begin() + HEADER_LENGTH, bytes_read.begin() + HEADER_LENGTH + parsed.total_len);

    const auto response_frame = co_await server.process_request(parsed, rest);
    co_await socket.async_send_to(asio::buffer(response_frame), sender, asio::use_awaitable);
}

} // namespace

UDPServer::UDPServer(asio::io_context& io_context, RequestRouter& router, std::string host, uint16_t port)
    : ServerBase(router),
      io_context_(io_context),
      host_(std::move(host)),
      port_(port),
      socket_(io_context_, asio::ip::udp::endpoint(asio::ip::make_address(host_), port_)) {
    set_transport_type("UDP");
}

asio::awaitable<void> UDPServer::serve() {
    running_ = true;
    co_await receive_loop();
}

asio::awaitable<void> UDPServer::receive_loop() {
    while (running_) {
        std::vector<uint8_t>  buffer(MAX_DATAGRAM_SIZE);
        asio::ip::udp::endpoint sender;
        const size_t length = co_await socket_.async_receive_from(asio::buffer(buffer), sender, asio::use_awaitable);
        buffer.resize(length);

        asio::co_spawn(io_context_, handle_datagram(std::move(buffer), sender, socket_, *this), asio::detached);
    }
}

void UDPServer::stop() {
    running_ = false;
    socket_.close();
}
