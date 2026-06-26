#pragma once

#include <memory>

#include <spdlog/formatter.h>

// Mirrors ekosis/logs/otlp_formatter.py's OtlpFormatter. Reads
// thread_local_span_key() (set ambient by the vendored asio patch, see
// documentation/ambient_span_context.md) instead of Python's ContextVar --
// same idea, different propagation mechanism. The JSON shape itself is
// MANDATORY, not user-configurable, same reasoning as the Python side: lets
// ekosis-log-shipper parse every line the same fixed way, zero format DSL.
class OtlpFormatter final : public spdlog::formatter {
public:
    void format(const spdlog::details::log_msg& msg, spdlog::memory_buf_t& dest) override;
    std::unique_ptr<spdlog::formatter> clone() const override;
};
