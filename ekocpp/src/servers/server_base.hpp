#pragma once

#include <string>
#include <vector>

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/binary_frame.hpp"
#include "../requests/request_router.hpp"
#include "../data_transfer_objects/response_dto.hpp"
#include "../data_transfer_objects/span_key.hpp"

// Mirrors ekosis/servers/server_base.py's ServerBase -- transport-agnostic.
// Owns the RequestRouter and builds the ResponseDTO envelope (success or
// error) for every request, regardless of which transport received it.
//
// Deliberate simplification vs. the Python side for now: RequestRouter::dispatch
// already returns a {status, data} json rather than throwing a RoutingExceptionBase
// hierarchy -- route_request() wraps that directly into a ResponseDTO instead of
// catching a routing-specific exception type. Partially revisited: a handler can
// now throw a ResponseException (e.g. ServerBusyException) to signal a specific
// status, caught separately in route_request() -- see exceptions.hpp.
class ServerBase {
public:
    explicit ServerBase(RequestRouter& router);

    void set_transport_type(std::string transport_type);
    const std::string& get_transport_type() const;

    // route_key/data are already known (sliced off the frame header, body
    // already msgpack-unpacked) before this is called -- see
    // build_parsing_error_response() for the case where that unpacking itself failed.
    asio::awaitable<ResponseDTO>          route_request(const SpanKey& span_key, const std::string& route_key, const nlohmann::json& data);

    ResponseDTO                           build_parsing_error_response(const SpanKey& span_key, const std::exception& error) const;

    // Shared by every transport's framing loop (stream and datagram alike):
    // given a parsed header and the body bytes that go with it, split
    // route_key/body, unpack, route, and pack the result back into a wire-ready
    // response frame. Transport-specific code only differs in how `rest` was
    // obtained and how the returned frame gets written back -- that part stays
    // in each transport's own file.
    asio::awaitable<std::vector<uint8_t>> process_request(const ParsedHeader& parsed, const std::vector<uint8_t>& rest);

protected:
    bool            running_ = false;
    RequestRouter&  router_;
    std::string     transport_type_;
};
