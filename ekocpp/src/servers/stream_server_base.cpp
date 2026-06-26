#include "stream_server_base.hpp"

#include <array>
#include <iostream>
#include <stdexcept>

#include "../data_transfer_objects/binary_frame.hpp"

template <typename SocketType>
asio::awaitable<void> handle_stream_connection(SocketType socket, ServerBase& server) {
    try {
        for (;;) {
            std::array<uint8_t, HEADER_LENGTH> header{};
            co_await asio::async_read(socket, asio::buffer(header), asio::use_awaitable);

            const ParsedHeader parsed = parse_header(header.data());
            co_await asio::this_coro::set_span_key(parsed.span_key);

            if (parsed.flags & PING_FLAG) {
                const auto pong = pack_ping_frame(parsed.span_key);
                co_await asio::async_write(socket, asio::buffer(pong), asio::use_awaitable);
                continue;
            }

            // total_len is attacker/bug-controlled (4 bytes straight off the wire,
            // max ~4GB) -- reject before allocating rather than let the allocation
            // itself throw further down.
            if (parsed.total_len > MAX_FRAME_SIZE) {
                const auto error_response = server.build_parsing_error_response(
                    parsed.span_key, std::length_error("total_len exceeds MAX_FRAME_SIZE")
                );
                const auto response_body  = nlohmann::json::to_msgpack(error_response.to_json());
                const auto response_frame = pack_frame(parsed.span_key, "", response_body);
                co_await asio::async_write(socket, asio::buffer(response_frame), asio::use_awaitable);
                break; // Can't trust this stream's framing beyond this point -- close it.
            }

            std::vector<uint8_t> rest(parsed.total_len);
            if (parsed.total_len > 0) {
                co_await asio::async_read(socket, asio::buffer(rest), asio::use_awaitable);
            }

            const auto response_frame = co_await server.process_request(parsed, rest);
            co_await asio::async_write(socket, asio::buffer(response_frame), asio::use_awaitable);
        }
    } catch (const std::system_error&) {
        // Expected: peer disconnected, RST, EOF mid-read -- asio reports these via
        // system_error. Drop this connection quietly, same as Python's
        // except (asyncio.IncompleteReadError, ConnectionResetError): break.
    } catch (const std::exception& e) {
        // NOT expected -- something genuinely wrong inside this connection's loop.
        // Don't let this look like a routine hangup. std::cerr is a stopgap until
        // spdlog is wired into ekocpp.
        std::cerr << "[ekocpp] unexpected error in stream connection handler: " << e.what() << "\n";
    }
}

template asio::awaitable<void> handle_stream_connection<asio::ip::tcp::socket>(asio::ip::tcp::socket, ServerBase&);
template asio::awaitable<void> handle_stream_connection<asio::local::stream_protocol::socket>(asio::local::stream_protocol::socket, ServerBase&);
