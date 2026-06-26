#pragma once

#include "../requests/request_router.hpp"

// Mirrors ekosis/standard_endpoints/log_manager.py. eco.log.buffer is a
// documented no-op here (see log_manager.cpp) -- spdlog's file sink has no
// runtime-adjustable buffer-size knob equivalent to Python's
// BufferedRotatingFileHandler.set_buffer_size; the closest things spdlog
// offers (flush_every/flush_on) are already wired in globally in
// EcoLogger::setup() and aren't per-call adjustable. Registered anyway
// (rather than omitted) so a client calling it gets a clear "not supported"
// response instead of ROUTE_KEY_UNKNOWN.
void register_log_manager_endpoints(RequestRouter& router);
