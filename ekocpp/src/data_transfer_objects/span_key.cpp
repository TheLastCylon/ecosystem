#include "span_key.hpp"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <random>

namespace {

// --------------------------------------------------------------------------------
void fill_random(uint8_t* buffer, size_t length) {
    static std::random_device random_device;
    std::uniform_int_distribution<int> byte_distribution(0, 255);
    for (size_t i = 0; i < length; ++i) {
        buffer[i] = static_cast<uint8_t>(byte_distribution(random_device));
    }
}

// --------------------------------------------------------------------------------
uint64_t load_big_endian_u64(const uint8_t* data) {
    uint64_t value = 0;
    for (int i = 0; i < 8; ++i) {
        value = (value << 8) | data[i];
    }
    return value;
}

// --------------------------------------------------------------------------------
void store_big_endian_u64(uint64_t value, uint8_t* out) {
    for (int i = 7; i >= 0; --i) {
        out[i] = static_cast<uint8_t>(value & 0xFF);
        value >>= 8;
    }
}

// --------------------------------------------------------------------------------
std::string bytes_to_hex(const uint8_t* data, size_t length) {
    static const char hex_digits[] = "0123456789abcdef";
    std::string result(length * 2, '0');
    for (size_t i = 0; i < length; ++i) {
        result[i * 2]     = hex_digits[(data[i] >> 4) & 0x0F];
        result[i * 2 + 1] = hex_digits[data[i] & 0x0F];
    }
    return result;
}

// --------------------------------------------------------------------------------
void hex_to_bytes(const std::string& hex, uint8_t* out) {
    for (size_t i = 0; i < hex.size() / 2; ++i) {
        out[i] = static_cast<uint8_t>(std::stoul(hex.substr(i * 2, 2), nullptr, 16));
    }
}

} // namespace

// --------------------------------------------------------------------------------
SpanKey SpanKey::generate() {
    SpanKey span_key;
    fill_random(span_key.trace_id.data(), span_key.trace_id.size());

    uint8_t span_id_bytes[8];
    fill_random(span_id_bytes, sizeof(span_id_bytes));
    span_key.span_id = load_big_endian_u64(span_id_bytes);

    return span_key;
}

// --------------------------------------------------------------------------------
SpanKey SpanKey::from_bytes(const uint8_t* data) {
    SpanKey span_key;
    std::memcpy(span_key.trace_id.data(), data, span_key.trace_id.size());
    span_key.span_id = load_big_endian_u64(data + 16);
    return span_key;
}

// --------------------------------------------------------------------------------
std::array<uint8_t, 24> SpanKey::to_bytes() const {
    std::array<uint8_t, 24> result{};
    std::memcpy(result.data(), trace_id.data(), trace_id.size());
    store_big_endian_u64(span_id, result.data() + 16);
    return result;
}

// --------------------------------------------------------------------------------
// Standard UUID string form (8-4-4-4-12 hex groups, dashed) for trace_id -- matches
// Python's str(uuid.UUID) exactly, so a printed SpanKey can be pasted straight into
// a Loki/Jaeger query.
std::string SpanKey::to_string() const {
    const std::string hex = bytes_to_hex(trace_id.data(), trace_id.size());
    const std::string trace_id_str =
        hex.substr(0, 8)  + "-" +
        hex.substr(8, 4)  + "-" +
        hex.substr(12, 4) + "-" +
        hex.substr(16, 4) + "-" +
        hex.substr(20, 12);

    char span_id_hex[17];
    std::snprintf(span_id_hex, sizeof(span_id_hex), "%016llx", static_cast<unsigned long long>(span_id));

    return trace_id_str + ":" + span_id_hex;
}

// --------------------------------------------------------------------------------
// Inverse of to_string() -- strips the dashes back out of the UUID portion,
// splits on the single ':' separator (UUID groups use '-', never ':', so the
// first/only ':' unambiguously marks the trace_id/span_id boundary).
SpanKey SpanKey::from_string(const std::string& text) {
    const size_t separator = text.find(':');

    std::string trace_id_str = text.substr(0, separator);
    trace_id_str.erase(std::remove(trace_id_str.begin(), trace_id_str.end(), '-'), trace_id_str.end());

    SpanKey span_key;
    hex_to_bytes(trace_id_str, span_key.trace_id.data());
    span_key.span_id = std::stoull(text.substr(separator + 1), nullptr, 16);
    return span_key;
}

// --------------------------------------------------------------------------------
std::string SpanKey::trace_id_hex() const {
    return bytes_to_hex(trace_id.data(), trace_id.size());
}

// --------------------------------------------------------------------------------
std::string SpanKey::span_id_hex() const {
    char buffer[17];
    std::snprintf(buffer, sizeof(buffer), "%016llx", static_cast<unsigned long long>(span_id));
    return buffer;
}

// --------------------------------------------------------------------------------
bool SpanKey::operator==(const SpanKey& other) const {
    return trace_id == other.trace_id && span_id == other.span_id;
}
