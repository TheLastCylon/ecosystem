#include "udp_client.hpp"

#include <asio.hpp>

namespace {
constexpr size_t MAX_DATAGRAM_SIZE = 65536; // Generously sized -- one UDP datagram, never fragmented at this layer.
}

// --------------------------------------------------------------------------------
UdpClient::UdpClient(std::string host, uint16_t port) : host_(std::move(host)), port_(port) {}

// --------------------------------------------------------------------------------
std::vector<uint8_t> UdpClient::send_and_receive(const std::vector<uint8_t>& request_frame) {
    asio::io_context        io_context;
    asio::ip::udp::resolver resolver(io_context);
    asio::ip::udp::socket   socket(io_context);

    const auto endpoints         = resolver.resolve(host_, std::to_string(port_));
    const auto receiver_endpoint = *endpoints.begin();

    socket.open(receiver_endpoint.endpoint().protocol());
    socket.send_to(asio::buffer(request_frame), receiver_endpoint);

    std::vector<uint8_t>    buffer(MAX_DATAGRAM_SIZE);
    asio::ip::udp::endpoint sender_endpoint;
    const size_t            length = socket.receive_from(asio::buffer(buffer), sender_endpoint);

    buffer.resize(length);
    return buffer;
}
