#include "tcp_client.hpp"
#include "binary_frame.hpp"

#include <asio.hpp>

// --------------------------------------------------------------------------------
TcpClient::TcpClient(std::string host, uint16_t port) : host_(std::move(host)), port_(port) {}

// --------------------------------------------------------------------------------
std::vector<uint8_t> TcpClient::send_and_receive(const std::vector<uint8_t>& request_frame) {
    asio::io_context        io_context;
    asio::ip::tcp::resolver resolver(io_context);
    asio::ip::tcp::socket   socket(io_context);

    asio::connect(socket, resolver.resolve(host_, std::to_string(port_)));
    asio::write(socket, asio::buffer(request_frame));

    std::vector<uint8_t> header(HEADER_LENGTH);
    asio::read(socket, asio::buffer(header));

    const ParsedHeader parsed = parse_header(header.data());

    std::vector<uint8_t> rest(parsed.total_len);
    if (parsed.total_len > 0) {
        asio::read(socket, asio::buffer(rest));
    }

    std::vector<uint8_t> response_frame;
    response_frame.reserve(HEADER_LENGTH + rest.size());
    response_frame.insert(response_frame.end(), header.begin(), header.end());
    response_frame.insert(response_frame.end(), rest.begin(), rest.end());
    return response_frame;
}
