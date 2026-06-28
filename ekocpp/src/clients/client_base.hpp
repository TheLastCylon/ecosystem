#pragma once

#include <chrono>
#include <cstdint>
#include <vector>

#include <asio.hpp>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/json_dto.hpp"
#include "../data_transfer_objects/span_key.hpp"

// Mirrors ekosis/clients/client_base.py's ClientBase -- the template-method
// algorithm every client shares: build the request frame, hand the raw bytes
// to the transport-specific retry loop (the one real seam, overridden per
// transport family below), parse the response frame, raise a typed exception
// on a non-SUCCESS status. This is the one place in the client/server split
// where real runtime polymorphism is earned -- code holding a ClientBase&
// can call send_message generically without knowing which transport it is.
class ClientBase {
public:
    explicit ClientBase(int max_retries = 3, std::chrono::milliseconds retry_delay = std::chrono::milliseconds{100});
    virtual ~ClientBase() = default;

    // Raw JSON overload -- internal implementation; also available directly when
    // a typed DTO is not appropriate (e.g. fire-and-forget, dynamic payloads).
    asio::awaitable<nlohmann::json> send_message(
        const std::string&    route_key,
        const nlohmann::json& data,
        SpanKey               span_key = SpanKey::generate()
    );

    // Typed overload with request data: caller passes a JsonDTO, gets a JsonDTO back.
    // to_json() / from_json() / validate() are handled internally -- no JSON at the call site.
    template <JsonDTO RequestDto, JsonDTO ResponseDto>
    asio::awaitable<ResponseDto> send_message(
        const std::string& route_key,
        const RequestDto&  data,
        SpanKey            span_key = SpanKey::generate()
    ) {
        const nlohmann::json response_data = co_await send_message(route_key, data.to_json(), span_key);
        ResponseDto result = ResponseDto::from_json(response_data);
        result.validate();
        co_return result;
    }

    // Typed overload without request data: for handlers that take no input (EmptyDto implied).
    template <JsonDTO ResponseDto>
    asio::awaitable<ResponseDto> send_message(
        const std::string& route_key,
        SpanKey            span_key = SpanKey::generate()
    ) {
        const nlohmann::json response_data = co_await send_message(route_key, nlohmann::json::object(), span_key);
        ResponseDto result = ResponseDto::from_json(response_data);
        result.validate();
        co_return result;
    }

protected:
    // The one abstract hook: given a packed request frame, return the packed
    // response frame, handling retries internally. Overridden once per
    // transport family (StreamClientBase, PersistentStreamClientBase,
    // DatagramClientBase) -- never directly by a leaf class.
    virtual asio::awaitable<std::vector<uint8_t>> send_message_retry_loop(std::vector<uint8_t> request) = 0;

    int                       max_retries_;
    std::chrono::milliseconds retry_delay_;
    int                       retry_count_ = 0;
    bool                      success_     = false;

private:
    [[noreturn]] static void throw_response_exception(int status, const nlohmann::json& data);
};
