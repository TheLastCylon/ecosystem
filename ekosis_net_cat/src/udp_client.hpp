#pragma once

#include <cstdint>
#include <string>
#include <vector>

// One-shot UDP client -- sends one datagram, reads one datagram back.
// Mirrors ekosis/clients/datagram_client_base.py's DatagramClientBase. No
// response timeout for v0.1 -- a manual debug tool that hangs on no response
// is exactly what `nc` itself does too; Ctrl+C is the timeout.
class UdpClient {
public:
    UdpClient(std::string host, uint16_t port);

    std::vector<uint8_t> send_and_receive(const std::vector<uint8_t>& request_frame);

private:
    std::string host_;
    uint16_t    port_;
};
