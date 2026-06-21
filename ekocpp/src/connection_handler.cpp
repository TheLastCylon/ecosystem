#include "connection_handler.hpp"

#include <array>
#include <exception>

#include "binary_frame.hpp"
#include "request_dto.hpp"

asio::awaitable<void> handle_connection(asio::ip::tcp::socket socket, RequestRouter& router) {
    try {
        for (;;) {
            std::array<uint8_t, HEADER_LENGTH> header{};
            co_await asio::async_read(socket, asio::buffer(header), asio::use_awaitable);

            const ParsedHeader parsed = parse_header(header.data());

            if (parsed.flags & PING_FLAG) {
                const auto pong = pack_ping_frame(parsed.span_key);
                co_await asio::async_write(socket, asio::buffer(pong), asio::use_awaitable);
                continue;
            }

            std::vector<uint8_t> rest(parsed.total_len);
            if (parsed.total_len > 0) {
                co_await asio::async_read(socket, asio::buffer(rest), asio::use_awaitable);
            }

            auto [route_key, body] = split_route_key_and_body(rest, parsed.route_key_len);

            RequestDTO dto = body.empty() ? RequestDTO{} : RequestDTO::from_msgpack(body.data(), body.size());

            RequestContext      request_context{parsed.span_key, dto};
            const nlohmann::json response_json = router.dispatch(route_key, request_context);

            const auto response_body  = nlohmann::json::to_msgpack(response_json);
            const auto response_frame = pack_frame(parsed.span_key, "", response_body);
            co_await asio::async_write(socket, asio::buffer(response_frame), asio::use_awaitable);
        }
    } catch (const std::exception&) {
        // Connection closed or framing error -- drop the connection, nothing left to route to.
    }
}
