#include "server_base.hpp"

#include <chrono>

#include <asio/awaitable.hpp>

#include "../data_transfer_objects/request_dto.hpp"
#include "../exceptions/exceptions.hpp"
#include "../requests/request_context.hpp"
#include "../requests/status.hpp"
#include "../state_keepers/statistics_keeper.hpp"

ServerBase::ServerBase(RequestRouter& router) : router_(router) {}

void ServerBase::set_transport_type(std::string transport_type) {
    transport_type_ = std::move(transport_type);
}

const std::string& ServerBase::get_transport_type() const {
    return transport_type_;
}

asio::awaitable<ResponseDTO> ServerBase::route_request(const SpanKey& span_key, const std::string& route_key, const nlohmann::json& data) {
    try {
        RequestDTO     dto{data, route_key};
        RequestContext request_context{span_key, dto};

        const auto           start  = std::chrono::steady_clock::now();
        const nlohmann::json result = co_await router_.dispatch(route_key, request_context);
        const double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        StatisticsKeeper::instance().add_endpoint_stats(route_key, elapsed);

        co_return ResponseDTO{span_key, result.at("status").get<int>(), result.at("data")};
    } catch (const ResponseException& e) {
        co_return ResponseDTO{span_key, e.status(), e.what()};
    } catch (const std::exception& e) {
        co_return ResponseDTO{span_key, static_cast<int>(Status::UNHANDLED), e.what()};
    }
}

ResponseDTO ServerBase::build_parsing_error_response(const SpanKey& span_key, const std::exception& error) const {
    return ResponseDTO{span_key, static_cast<int>(Status::PROTOCOL_PARSING_ERROR), error.what()};
}

asio::awaitable<std::vector<uint8_t>> ServerBase::process_request(const ParsedHeader& parsed, const std::vector<uint8_t>& rest) {
    auto [route_key, body] = split_route_key_and_body(rest, parsed.route_key_len);

    ResponseDTO response;
    try {
        const nlohmann::json data = body.empty() ? nlohmann::json::object() : nlohmann::json::from_msgpack(body);
        response = co_await route_request(parsed.span_key, route_key, data);
    } catch (const std::exception& e) {
        response = build_parsing_error_response(parsed.span_key, e);
    }

    const auto response_body = nlohmann::json::to_msgpack(response.to_json());
    co_return pack_frame(parsed.span_key, "", response_body);
}
