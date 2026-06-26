#include "log_manager.hpp"

#include <spdlog/spdlog.h>

#include "../logs/eco_logger.hpp"

namespace {

RequestDTO eco_log_level(SpanKey, RequestDTO& dto) {
    const std::string level = dto.data.at("level").get<std::string>();
    EcoLogger::instance().set_level(level);
    return RequestDTO{{{"level", level}}};
}

RequestDTO eco_log_buffer(SpanKey, RequestDTO& dto) {
    const int size = dto.data.value("size", 0);
    spdlog::warn("eco.log.buffer called with size [{}] -- no-op on ekocpp, spdlog's file sink has no runtime buffer-size knob.", size);
    return RequestDTO{{{"size", size}, {"applied", false}}};
}

} // namespace

void register_log_manager_endpoints(RequestRouter& router) {
    router.register_endpoint("eco.log.level", eco_log_level);
    router.register_endpoint("eco.log.buffer", eco_log_buffer);
}
