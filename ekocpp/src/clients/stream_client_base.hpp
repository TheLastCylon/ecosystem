#pragma once

#include <chrono>

#include "client_base.hpp"

// Mirrors ekosis/clients/stream_client_base.py's StreamClientBase --
// transient: open a fresh connection, write the request, read exactly one
// response frame, close. Templated on SocketType (asio::ip::tcp::socket vs.
// asio::local::stream_protocol::socket) since both support the same
// async_read/async_write/async_connect calls but are distinct concrete
// types -- TCP and UDS share this body, each as its own instantiation
// overriding ClientBase::send_message_retry_loop in its own right.
template <typename SocketType>
class StreamClientBase : public ClientBase {
public:
    explicit StreamClientBase(
        std::chrono::milliseconds timeout     = std::chrono::seconds{5},
        int                       max_retries = 3,
        std::chrono::milliseconds retry_delay = std::chrono::milliseconds{100}
    );

protected:
    // The remaining abstract hook -- how to obtain a connected socket.
    // Concrete per leaf class (TransientTCPClient/TransientUDSClient).
    virtual asio::awaitable<SocketType> open_connection() = 0;

    asio::awaitable<std::vector<uint8_t>> send_message_retry_loop(std::vector<uint8_t> request) override;

private:
    asio::awaitable<std::vector<uint8_t>> send_message_once(const std::vector<uint8_t>& request);

    std::chrono::milliseconds timeout_;
};
