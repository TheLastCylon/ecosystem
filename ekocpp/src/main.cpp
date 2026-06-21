#include <asio.hpp>
#include <iostream>

#include "connection_handler.hpp"
#include "request_router.hpp"

namespace {

// A handler declaring both injectable types, in order -- the simplest
// possible proof that function_traits-based dispatch is wired end to end.
// Returns the received body straight back, so the round trip is visible.
nlohmann::json echo_handler(SpanKey span_key, RequestDTO& dto) {
    std::cout << "[" << span_key.to_string() << "] " << dto.data.dump() << std::endl;
    return dto.data;
}

asio::awaitable<void> listen(asio::ip::tcp::acceptor acceptor, RequestRouter& router) {
    for (;;) {
        auto socket = co_await acceptor.async_accept(asio::use_awaitable);
        asio::co_spawn(acceptor.get_executor(), handle_connection(std::move(socket), router), asio::detached);
    }
}

} // namespace

int main() {
    asio::io_context io_context(1);

    RequestRouter router;
    router.register_endpoint("echo", echo_handler);

    asio::ip::tcp::acceptor acceptor(io_context, asio::ip::tcp::endpoint(asio::ip::tcp::v4(), 9999));
    asio::co_spawn(io_context, listen(std::move(acceptor), router), asio::detached);

    io_context.run();
    return 0;
}
