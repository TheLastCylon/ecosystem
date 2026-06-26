#include "ambient_span_context.hpp"

// --------------------------------------------------------------------------------
SpanKey& thread_local_span_key() {
    thread_local SpanKey current;
    return current;
}
