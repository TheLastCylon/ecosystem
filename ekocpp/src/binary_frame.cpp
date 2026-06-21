#include "binary_frame.hpp"

#include <cstring>

namespace {

// --------------------------------------------------------------------------------
void store_big_endian_u32(uint32_t value, uint8_t* out) {
    out[0] = static_cast<uint8_t>((value >> 24) & 0xFF);
    out[1] = static_cast<uint8_t>((value >> 16) & 0xFF);
    out[2] = static_cast<uint8_t>((value >> 8)  & 0xFF);
    out[3] = static_cast<uint8_t>(value         & 0xFF);
}

// --------------------------------------------------------------------------------
uint32_t load_big_endian_u32(const uint8_t* data) {
    return (static_cast<uint32_t>(data[0]) << 24) |
           (static_cast<uint32_t>(data[1]) << 16) |
           (static_cast<uint32_t>(data[2]) << 8)  |
            static_cast<uint32_t>(data[3]);
}

} // namespace

// --------------------------------------------------------------------------------
std::vector<uint8_t> pack_frame(
    const SpanKey& span_key, const std::string& route_key, const std::vector<uint8_t>& body, uint8_t flags
) {
    const auto     span_key_bytes = span_key.to_bytes();
    const uint8_t  route_key_len  = static_cast<uint8_t>(route_key.size());
    const uint32_t total_len      = static_cast<uint32_t>(route_key.size() + body.size());

    std::vector<uint8_t> frame;
    frame.reserve(HEADER_LENGTH + route_key.size() + body.size());

    frame.insert(frame.end(), span_key_bytes.begin(), span_key_bytes.end());

    uint8_t length_bytes[4];
    store_big_endian_u32(total_len, length_bytes);
    frame.insert(frame.end(), length_bytes, length_bytes + 4);

    frame.push_back(route_key_len);
    frame.push_back(flags);
    frame.push_back(0); // reserved
    frame.push_back(0); // reserved

    frame.insert(frame.end(), route_key.begin(), route_key.end());
    frame.insert(frame.end(), body.begin(), body.end());

    return frame;
}

// --------------------------------------------------------------------------------
ParsedHeader parse_header(const uint8_t* header) {
    ParsedHeader parsed;
    parsed.span_key      = SpanKey::from_bytes(header);
    parsed.total_len     = load_big_endian_u32(header + 24);
    parsed.route_key_len = header[28];
    parsed.flags         = header[29];
    return parsed;
}

// --------------------------------------------------------------------------------
std::pair<std::string, std::vector<uint8_t>> split_route_key_and_body(
    const std::vector<uint8_t>& data, uint8_t route_key_len
) {
    std::string route_key(data.begin(), data.begin() + route_key_len);
    std::vector<uint8_t> body(data.begin() + route_key_len, data.end());
    return { route_key, body };
}

// --------------------------------------------------------------------------------
std::vector<uint8_t> pack_ping_frame(const SpanKey& span_key) {
    return pack_frame(span_key, "", {}, PING_FLAG);
}
