#pragma once

#include <nlohmann/json.hpp>

#include "span_key.hpp"

// Mirrors ekosis/data_transfer_objects/json_protocol.py's ResponseDTO --
// the envelope every route_request() call returns, success or failure.
// span_key is populated from the wire frame header after unpacking, not from
// the json body -- mirrors Python's `span_key: SpanKey | None = None` default.
// from_json() therefore produces a default (all-zero) span_key, which callers
// populate externally; to_json() omits it, matching the wire response format.
struct ResponseDTO {
    SpanKey        span_key;
    int            status;
    nlohmann::json data;

    nlohmann::json to_json() const {
        return { {"status", status}, {"data", data} };
    }

    static ResponseDTO from_json(const nlohmann::json& j) {
        return { SpanKey{}, j.at("status").get<int>(), j.at("data") };
    }
};
