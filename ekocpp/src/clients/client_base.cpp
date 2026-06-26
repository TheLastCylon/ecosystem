#include "client_base.hpp"

#include "../data_transfer_objects/binary_frame.hpp"
#include "../exceptions/exceptions.hpp"
#include "../requests/status.hpp"

ClientBase::ClientBase(int max_retries, std::chrono::milliseconds retry_delay)
    : max_retries_(max_retries), retry_delay_(retry_delay) {}

asio::awaitable<nlohmann::json> ClientBase::send_message(const std::string& route_key, const nlohmann::json& data, SpanKey span_key) {
    success_     = false;
    retry_count_ = 0;

    const auto request_body  = nlohmann::json::to_msgpack(data);
    const auto request_frame = pack_frame(span_key, route_key, request_body);

    const auto response_frame = co_await send_message_retry_loop(request_frame);

    const ParsedHeader    parsed = parse_header(response_frame.data());
    std::vector<uint8_t>  rest(response_frame.begin() + HEADER_LENGTH, response_frame.begin() + HEADER_LENGTH + parsed.total_len);
    auto [ignored_route_key, body] = split_route_key_and_body(rest, parsed.route_key_len);

    const nlohmann::json response_json = nlohmann::json::from_msgpack(body);
    const int            status        = response_json.at("status").get<int>();
    const nlohmann::json response_data = response_json.at("data");

    if (status != static_cast<int>(Status::SUCCESS)) {
        throw_response_exception(status, response_data);
    }

    co_return response_data;
}

void ClientBase::throw_response_exception(int status, const nlohmann::json& data) {
    const std::string message = data.is_string() ? data.get<std::string>() : data.dump();

    switch (static_cast<Status>(status)) {
        case Status::PROTOCOL_PARSING_ERROR:    throw ProtocolParsingException(message);
        case Status::CLIENT_DENIED:             throw ClientDeniedException(message);
        case Status::PYDANTIC_VALIDATION_ERROR: throw PydanticValidationException(message);
        case Status::ROUTE_KEY_UNKNOWN:          throw RouteKeyUnknownException(message);
        case Status::APPLICATION_BUSY:          throw ServerBusyException(message);
        case Status::PROCESSING_FAILURE:        throw ProcessingException(message);
        case Status::UNHANDLED:                 throw UnhandledException(message);
    }
    throw UnknownStatusCodeException("Unrecognised status code [" + std::to_string(status) + "]: " + message);
}
