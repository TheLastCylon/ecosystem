#pragma once

#include <cstdint>
#include <vector>

#include <nlohmann/json.hpp>

// Body payload, MessagePack-encoded on the wire (Protocol v1). Schemaless,
// same data model as the Python side's Pydantic DTOs -- no codegen step.
// span_key and route_key live in RequestContext; this struct carries only the
// data payload, consistent with the C++ split of framing metadata vs. payload.
struct RequestDTO {
    nlohmann::json data;

    static RequestDTO from_msgpack(const uint8_t* data_ptr, size_t length) {
        RequestDTO dto;
        dto.data = nlohmann::json::from_msgpack(data_ptr, data_ptr + length);
        return dto;
    }

    std::vector<uint8_t> to_msgpack() const {
        return nlohmann::json::to_msgpack(data);
    }

    nlohmann::json     to_json()                        const { return data; }
    static RequestDTO  from_json(const nlohmann::json& j)     { return {j}; }
};
