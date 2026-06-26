#include "buffered_handler_manager.hpp"

namespace {

using HandlerRegistry = std::unordered_map<std::string, std::shared_ptr<BufferedHandlerInterface>>;

nlohmann::json handler_info_json(BufferedHandlerInterface& handler) {
    return {
        {"route_key", handler.route_key()},
        {"receiving_paused", handler.is_receiving_paused()},
        {"processing_paused", handler.is_processing_paused()},
        {"database_sizes", {{"pending", handler.pending_queue_size()}, {"error", handler.error_queue_size()}}},
    };
}

std::shared_ptr<BufferedHandlerInterface> find_handler(HandlerRegistry& registry, const std::string& route_key) {
    auto it = registry.find(route_key);
    return it == registry.end() ? nullptr : it->second;
}

nlohmann::json not_found(const std::string& route_key) {
    return {{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No queue for route key: [" + route_key + "]"}};
}

nlohmann::json with_handler_info(BufferedHandlerInterface& handler, const std::string& message) {
    return {{"queue_data", handler_info_json(handler)}, {"message", message}};
}

} // namespace

void register_buffered_handler_management_endpoints(RequestRouter& router, HandlerRegistry& registry) {
    router.register_endpoint("eco.buffered_handler.data", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        return RequestDTO{{
            {"queue_data", handler_info_json(*handler)},
            {"request_data", nullptr},
            {"message", "Buffered Endpoint[" + route_key + "]: Data retrieved."},
        }};
    });

    router.register_endpoint("eco.buffered_handler.receiving.pause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->pause_receiving();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: Paused RECEIVING.")};
    });

    router.register_endpoint("eco.buffered_handler.receiving.unpause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->unpause_receiving();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: UN-Paused RECEIVING.")};
    });

    router.register_endpoint("eco.buffered_handler.processing.pause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->pause_processing();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: Paused PROCESSING.")};
    });

    router.register_endpoint("eco.buffered_handler.processing.unpause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->unpause_processing();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: UN-Paused PROCESSING.")};
    });

    router.register_endpoint("eco.buffered_handler.all.pause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->pause_receiving();
        handler->pause_processing();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: Paused ALL.")};
    });

    router.register_endpoint("eco.buffered_handler.all.unpause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->unpause_receiving();
        handler->unpause_processing();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: UN-Paused ALL.")};
    });

    router.register_endpoint("eco.buffered_handler.errors.get_first_10", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        return RequestDTO{{
            {"queue_data", handler->get_first_x_error_span_keys(10)},
            {"message", "Buffered Endpoint[" + route_key + "]: Retrieved first 10 span-keys for error database."},
        }};
    });

    router.register_endpoint("eco.buffered_handler.errors.reprocess.all", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->reprocess_error_queue();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: Error database entries, moved to incoming database.")};
    });

    router.register_endpoint("eco.buffered_handler.errors.clear", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               handler   = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};
        handler->error_queue_clear();
        return RequestDTO{with_handler_info(*handler, "Buffered Endpoint[" + route_key + "]: Error database cleared.")};
    });

    router.register_endpoint("eco.buffered_handler.errors.reprocess.one", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key      = dto.data.at("queue_route_key").get<std::string>();
        const std::string span_key_string = dto.data.at("span_key").get<std::string>();
        auto               handler        = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};

        auto result = handler->reprocess_error_queue_span_key(SpanKey::from_string(span_key_string));
        if (!result) {
            return RequestDTO{{{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No request with span-key [" + span_key_string + "] in error queue for route key: [" + route_key + "]"}}};
        }
        return RequestDTO{{
            {"queue_data", handler_info_json(*handler)},
            {"request_data", *result},
            {"message", "Buffered Endpoint[" + route_key + "]: Error database entry[" + span_key_string + "] moved to incoming database."},
        }};
    });

    router.register_endpoint("eco.buffered_handler.errors.pop_request", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key      = dto.data.at("queue_route_key").get<std::string>();
        const std::string span_key_string = dto.data.at("span_key").get<std::string>();
        auto               handler        = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};

        auto result = handler->pop_request_from_error_queue(SpanKey::from_string(span_key_string));
        if (!result) {
            return RequestDTO{{{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No request with span-key [" + span_key_string + "] in error queue for route key: [" + route_key + "]"}}};
        }
        return RequestDTO{{
            {"queue_data", handler_info_json(*handler)},
            {"request_data", *result},
            {"message", "Buffered Endpoint[" + route_key + "]: POPPED Error database entry[" + span_key_string + "]."},
        }};
    });

    router.register_endpoint("eco.buffered_handler.errors.inspect_request", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key      = dto.data.at("queue_route_key").get<std::string>();
        const std::string span_key_string = dto.data.at("span_key").get<std::string>();
        auto               handler        = find_handler(registry, route_key);
        if (!handler) return RequestDTO{not_found(route_key)};

        auto result = handler->inspect_request_in_error_queue(SpanKey::from_string(span_key_string));
        if (!result) {
            return RequestDTO{{{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No request with span-key [" + span_key_string + "] in error queue for route key: [" + route_key + "]"}}};
        }
        return RequestDTO{{
            {"queue_data", handler_info_json(*handler)},
            {"request_data", *result},
            {"message", "Buffered Endpoint[" + route_key + "]: INSPECTING Error database entry[" + span_key_string + "]."},
        }};
    });
}
