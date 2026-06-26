#pragma once

#include <memory>
#include <string>
#include <unordered_map>

#include "../requests/request_router.hpp"
#include "../sending/buffered_sender.hpp"

// Mirrors ekosis/standard_endpoints/buffered_sender_manager.py. Same
// reference-to-registry approach as buffered_handler_manager.hpp -- no
// BufferedSenderKeeper singleton needed, ApplicationBase owns the registry
// directly. Simpler than the handler side: BufferedSender is already
// concrete (no template), so no type-erasure interface is needed either.
void register_buffered_sender_management_endpoints(
    RequestRouter& router,
    std::unordered_map<std::string, std::shared_ptr<BufferedSender>>& registry
);
