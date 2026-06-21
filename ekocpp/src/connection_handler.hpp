#pragma once

#include <asio.hpp>

#include "request_router.hpp"

// One coroutine per accepted connection. Reads frames in the locked Protocol
// v1 shape ([24B SpanKey][4B total_len][1B route_key_len][1B flags]
// [2B reserved][route_key][body]), answers PING_FLAG frames directly without
// ever reaching the router, and dispatches everything else.
asio::awaitable<void> handle_connection(asio::ip::tcp::socket socket, RequestRouter& router);
