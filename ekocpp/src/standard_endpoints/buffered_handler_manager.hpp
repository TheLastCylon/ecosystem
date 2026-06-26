#pragma once

#include <memory>
#include <string>
#include <unordered_map>

#include "../requests/buffered_handler_interface.hpp"
#include "../requests/request_router.hpp"

// Mirrors ekosis/standard_endpoints/buffered_handler_manager.py. Takes the
// route-key registry by reference rather than reaching for a
// BufferedHandlerKeeper singleton -- ApplicationBase owns this registry
// directly (see application_base.hpp's comment on buffered_handler_registry_).
// Registered once from ApplicationBase's constructor; the registry is empty
// at that exact moment (the derived app's register_buffered_endpoint calls
// haven't run yet), but that's fine -- these lambdas capture the registry
// by reference and only read it later, at actual request time.
void register_buffered_handler_management_endpoints(
    RequestRouter& router,
    std::unordered_map<std::string, std::shared_ptr<BufferedHandlerInterface>>& registry
);
