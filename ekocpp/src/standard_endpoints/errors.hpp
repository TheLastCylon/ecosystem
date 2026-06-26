#pragma once

#include "../requests/request_router.hpp"

// Mirrors ekosis/standard_endpoints/errors.py. Registers directly onto a
// RequestRouter& rather than via decorator-triggered import side effects
// (no decorator-based registration exists in ekocpp -- same explicit-call
// reasoning already applied to register_endpoint/register_buffered_endpoint).
// Called once from ApplicationBase's constructor.
void register_error_endpoints(RequestRouter& router);
