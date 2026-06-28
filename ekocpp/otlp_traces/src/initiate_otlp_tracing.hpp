#pragma once

// Mirrors ekosis_otlp_traces/setup.py's initiate_otlp_tracing().
// Reads ECOENV_EXTRA_OTLP_TRACES_ENDPOINT, constructs OtlpTracingMiddleware +
// OtlpBufferedTracingMiddleware, and registers both with their respective
// singleton managers. Call once from the application constructor, after
// AppConfiguration::initialize().
void initiate_otlp_tracing();
