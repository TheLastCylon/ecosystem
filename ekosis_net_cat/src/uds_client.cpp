#include "uds_client.hpp"
#include "binary_frame.hpp"

#include <asio.hpp>

// --------------------------------------------------------------------------------
UdsClient::UdsClient(std::string socket_path) : socket_path_(std::move(socket_path)) {}

// --------------------------------------------------------------------------------
std::vector<uint8_t> UdsClient::send_and_receive(const std::vector<uint8_t>& request_frame) {
    asio::io_context                     io_context;
    asio::local::stream_protocol::socket socket(io_context);

    socket.connect(asio::local::stream_protocol::endpoint(socket_path_));
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
