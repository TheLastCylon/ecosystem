#include "initiate_otlp_tracing.hpp"

#include <memory>
#include <string>

#include "configuration/config_models.hpp"
#include "middleware/middleware_manager.hpp"
#include "middleware/buffered_middleware_manager.hpp"
#include "otlp_tracing_middleware.hpp"
#include "otlp_buffered_tracing_middleware.hpp"

void initiate_otlp_tracing() {
    const AppConfiguration& config       = AppConfiguration::instance();
    const std::string       endpoint     = config.extra("OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces");
    const std::string       service_name = config.name() + "-" + config.instance_id();

    std::shared_ptr<OtlpTracingMiddleware> tracer =
        std::make_shared<OtlpTracingMiddleware>(endpoint, service_name);

    MiddlewareManager::instance().add(tracer);
    BufferedMiddlewareManager::instance().add(
        std::make_shared<OtlpBufferedTracingMiddleware>(tracer)
    );
}
