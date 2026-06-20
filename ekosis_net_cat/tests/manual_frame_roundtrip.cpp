#include "span_key.hpp"
#include "binary_frame.hpp"

#include <cassert>
#include <iostream>

// No live server needed -- this only proves the frame pack/parse round trip and
// the ping/pong shape are self-consistent, mirroring binary_protocol_tests.py's
// intent on the Python side. Cross-language byte-for-byte agreement with the
// Python implementation was verified manually during development.
int main() {
    const SpanKey               span_key = SpanKey::generate();
    const std::vector<uint8_t>  body     = {0x81, 0xa7, 'm','e','s','s','a','g','e', 0xa4,'t','e','s','t'};
    const auto                  frame    = pack_frame(span_key, "echo", body);

    const ParsedHeader parsed = parse_header(frame.data());
    assert(parsed.span_key == span_key);
    assert(parsed.route_key_len == 4);
    assert(parsed.total_len == 4 + body.size());
    assert(parsed.flags == 0);

    const std::vector<uint8_t> rest(frame.begin() + HEADER_LENGTH, frame.end());
    const auto [route_key, parsed_body] = split_route_key_and_body(rest, parsed.route_key_len);
    assert(route_key == "echo");
    assert(parsed_body == body);

    const auto ping        = pack_ping_frame(span_key);
    const ParsedHeader ping_parsed = parse_header(ping.data());
    assert(ping.size() == HEADER_LENGTH);
    assert(ping_parsed.flags & PING_FLAG);
    assert(ping_parsed.total_len == 0);

    std::cout << "manual_frame_roundtrip: all assertions passed\n";
    return 0;
}
