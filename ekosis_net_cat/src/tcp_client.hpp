#pragma once

#include <cstdint>
#include <string>
#include <vector>

// One-shot, transient TCP client -- connects, sends one frame, reads one frame
// back, disconnects. Mirrors ekosis/clients/transient_tcp.py's TransientTCPClient.
class TcpClient {
public:
    TcpClient(std::string host, uint16_t port);

    std::vector<uint8_t> send_and_receive(const std::vector<uint8_t>& request_frame);

private:
    std::string host_;
    uint16_t    port_;
};
