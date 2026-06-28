#pragma once

#include <cstdint>
#include <vector>

#include <nlohmann/json.hpp>

// Mirrors ekosis/data_transfer_objects/json_protocol.py's RequestDTO.
// route_key comes from the binary frame header and is set by the server
// after parsing -- it is NOT encoded in the MessagePack body (body carries
// data only, consistent with the wire protocol's header/body split).
// All internal response DTOs (standard_endpoints) leave route_key as ""
// since to_json() only serialises data.
struct RequestDTO {
    nlohmann::json data;
    std::string    route_key;

    static RequestDTO from_msgpack(const uint8_t* data_ptr, size_t length) {
        RequestDTO dto;
        dto.data = nlohmann::json::from_msgpack(data_ptr, data_ptr + length);
        return dto; // route_key set separately from the frame header
    }

    std::vector<uint8_t> to_msgpack() const {
        return nlohmann::json::to_msgpack(data);
    }

    nlohmann::json     to_json()                        const { return data; }
    static RequestDTO  from_json(const nlohmann::json& j)     { return {j}; }
    void               validate()                       const {}
};
