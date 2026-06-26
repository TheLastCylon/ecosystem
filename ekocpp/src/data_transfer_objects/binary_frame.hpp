#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include "span_key.hpp"

// Mirrors ekosis/data_transfer_objects/binary_frame.py exactly --
// [24B SpanKey][4B total_len][1B route_key_len][1B flags][2B reserved][route_key][body]

constexpr size_t  HEADER_LENGTH = 32;
constexpr uint8_t PING_FLAG     = 0x01; // Liveness probe -- answered by the transport layer alone, never routed.

// total_len is a 4-byte field straight off the wire (max ~4GB) with nothing
// else bounding it. Without this, a client claiming a huge total_len drives
// an unbounded allocation on the stream path, or -- worse, on the UDP path --
// out-of-bounds iterator arithmetic past the actual received datagram.
// 16MB is generous for any current ekosis/ekocpp payload; revisit if a real
// use case needs more.
constexpr uint32_t MAX_FRAME_SIZE = 16 * 1024 * 1024;

struct ParsedHeader {
    SpanKey  span_key;
    uint8_t  route_key_len;
    uint32_t total_len;
    uint8_t  flags;
};

std::vector<uint8_t> pack_frame(
    const SpanKey&              span_key,
    const std::string&          route_key,
    const std::vector<uint8_t>& body,
    uint8_t                     flags = 0
);

// header must point at exactly HEADER_LENGTH readable bytes.
ParsedHeader parse_header(const uint8_t* header);

std::pair<std::string, std::vector<uint8_t>> split_route_key_and_body(
    const std::vector<uint8_t>& data,
    uint8_t                     route_key_len
);

// A ping/pong frame: no route_key, no body, PING_FLAG set -- a pure 32-byte
// liveness probe. Same shape used in both directions.
std::vector<uint8_t> pack_ping_frame(const SpanKey& span_key);
