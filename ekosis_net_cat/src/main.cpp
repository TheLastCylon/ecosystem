#include "span_key.hpp"
#include "binary_frame.hpp"
#include "tcp_client.hpp"
#include "udp_client.hpp"
#include "uds_client.hpp"

#include <nlohmann/json.hpp>

#include <cstdint>
#include <iostream>
#include <string>

namespace {

// --------------------------------------------------------------------------------
std::string status_to_string(int status) {
    switch (status) {
        case 0:   return "SUCCESS";
        case 100: return "PROTOCOL_PARSING_ERROR";
        case 200: return "CLIENT_DENIED";
        case 300: return "PYDANTIC_VALIDATION_ERROR";
        case 400: return "ROUTE_KEY_UNKNOWN";
        case 500: return "APPLICATION_BUSY";
        case 600: return "PROCESSING_FAILURE";
        case 999: return "UNHANDLED";
        default:  return "UNKNOWN_STATUS";
    }
}

// --------------------------------------------------------------------------------
void print_usage() {
    std::cerr <<
        "usage: esnc <tcp|udp|uds> <target> <route_key> [data_json]\n"
        "\n"
        "  target     : host:port for tcp/udp, a socket path for uds\n"
        "  route_key  : the route to send the request to\n"
        "  data_json  : the request payload, as a JSON string (default '{}')\n"
        "\n"
        "examples:\n"
        "  esnc tcp 127.0.0.1:8888 echo '{\"message\": \"hi\"}'\n"
        "  esnc udp 127.0.0.1:8889 echo '{\"message\": \"hi\"}'\n"
        "  esnc uds /tmp/echo_example_0.uds.sock echo '{\"message\": \"hi\"}'\n";
}

// --------------------------------------------------------------------------------
std::pair<std::string, uint16_t> split_host_port(const std::string& target) {
    const auto separator = target.rfind(':');
    if (separator == std::string::npos) {
        throw std::runtime_error("target must be in host:port form, got: " + target);
    }
    return { target.substr(0, separator), static_cast<uint16_t>(std::stoi(target.substr(separator + 1))) };
}

// --------------------------------------------------------------------------------
std::vector<uint8_t> send_request(
    const std::string& transport, const std::string& target, const std::vector<uint8_t>& request_frame
) {
    if (transport == "tcp") {
        const auto [host, port] = split_host_port(target);
        return TcpClient(host, port).send_and_receive(request_frame);
    }
    if (transport == "udp") {
        const auto [host, port] = split_host_port(target);
        return UdpClient(host, port).send_and_receive(request_frame);
    }
    if (transport == "uds") {
        return UdsClient(target).send_and_receive(request_frame);
    }
    throw std::runtime_error("unknown transport '" + transport + "' -- expected tcp, udp, or uds");
}

} // namespace

// --------------------------------------------------------------------------------
int main(int argc, char** argv) {
    if (argc < 4) {
        print_usage();
        return 1;
    }

    const std::string transport = argv[1];
    const std::string target    = argv[2];
    const std::string route_key = argv[3];
    const std::string data_json = argc > 4 ? argv[4] : "{}";

    try {
        const nlohmann::json data = nlohmann::json::parse(data_json);
        const SpanKey         span_key      = SpanKey::generate();
        const auto            body          = nlohmann::json::to_msgpack(data);
        const auto            request_frame = pack_frame(span_key, route_key, body);

        std::cout << "Sending : span_key=[" << span_key.to_string() << "] "
                   << "route_key=[" << route_key << "] data=" << data.dump() << "\n";

        const auto response_frame = send_request(transport, target, request_frame);

        const ParsedHeader          parsed = parse_header(response_frame.data());
        const std::vector<uint8_t>  rest(response_frame.begin() + HEADER_LENGTH, response_frame.end());
        const auto [response_route_key, response_body] = split_route_key_and_body(rest, parsed.route_key_len);
        const nlohmann::json        response_json = nlohmann::json::from_msgpack(response_body);

        const int status = response_json.at("status").get<int>();
        std::cout << "Response: span_key=[" << parsed.span_key.to_string() << "] "
                   << "status=[" << status << " " << status_to_string(status) << "] "
                   << "data=" << response_json.at("data").dump() << "\n";

        return status == 0 ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "ERROR   : " << e.what() << "\n";
        return 1;
    }
}
