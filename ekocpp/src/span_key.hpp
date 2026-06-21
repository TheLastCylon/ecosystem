#pragma once

#include <array>
#include <cstdint>
#include <string>

// Mirrors ekosis/data_transfer_objects/json_protocol.py's SpanKey + span_id.py's
// SpanId -- a 16-byte trace_id (standard UUID, big-endian/network byte order) +
// an 8-byte span_id (big-endian uint64). Together: the canonical 24-byte identity
// of a span, as it appears in the first 24 bytes of every binary frame header.
class SpanKey {
public:
    std::array<uint8_t, 16> trace_id{};
    uint64_t                span_id = 0;

    static SpanKey generate();
    static SpanKey from_bytes(const uint8_t* data); // exactly 24 bytes: 16 trace_id + 8 span_id

    std::array<uint8_t, 24> to_bytes() const;
    std::string             to_string() const; // "{trace_id-as-uuid}:{span_id-as-16-hex-chars}"

    bool operator==(const SpanKey& other) const;
};
