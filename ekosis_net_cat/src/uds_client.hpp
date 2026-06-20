#pragma once

#include <cstdint>
#include <string>
#include <vector>

// One-shot, transient UDS client -- connects, sends one frame, reads one frame
// back, disconnects. Mirrors ekosis/clients/transient_uds.py's TransientUDSClient.
class UdsClient {
public:
    explicit UdsClient(std::string socket_path);

    std::vector<uint8_t> send_and_receive(const std::vector<uint8_t>& request_frame);

private:
    std::string socket_path_;
};
