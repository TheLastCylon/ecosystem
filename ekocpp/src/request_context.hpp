#pragma once

#include "request_dto.hpp"
#include "span_key.hpp"

// Per-request data a registered handler may ask for, by declaring it as a
// parameter. Named RequestContext (not EndpointContext) because the same
// resolve-by-type mechanism is expected to extend to buffered/queued
// handlers later, not just standard endpoints.
struct RequestContext {
    SpanKey      span_key;
    RequestDTO&  dto;
};
