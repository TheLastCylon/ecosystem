#pragma once

#include <array>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>

#include <nlohmann/json.hpp>

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
    static SpanKey from_string(const std::string& text); // inverse of to_string()

    std::array<uint8_t, 24> to_bytes() const;
    std::string             to_string() const; // "{trace_id-as-uuid}:{span_id-as-16-hex-chars}"

    // Plain hex, no dashes/colon -- OTel's own trace_id/span_id wire
    // convention, matching Python's uuid.UUID.hex / SpanId.hex exactly.
    std::string trace_id_hex() const; // 32 hex chars
    std::string span_id_hex() const;  // 16 hex chars

    bool operator==(const SpanKey& other) const;

    // For the queue's own on-disk JSON (ekocpp-local SQLite files, never
    // exchanged with Python directly) -- round-trips through to_string(),
    // not Python's {trace_id, span_id} field layout, since nothing outside
    // this process ever reads it.
    nlohmann::json to_json() const { return nlohmann::json(to_string()); }
    static SpanKey from_json(const nlohmann::json& j) { return from_string(j.get<std::string>()); }
    void           validate()                    const {}
};

namespace std {
// Mirrors Python's SpanKey.__hash__ (hash(self.bytes)) -- hashes the raw 24
// bytes directly, so SpanKey can key an unordered_map/unordered_set instead
// of QueuePage's Python original needing a linear scan to find an entry.
template <>
struct hash<SpanKey> {
    size_t operator()(const SpanKey& key) const noexcept {
        const std::array<uint8_t, 24> bytes = key.to_bytes();
        return std::hash<std::string_view>{}(
            std::string_view(reinterpret_cast<const char*>(bytes.data()), bytes.size())
        );
    }
};
} // namespace std
