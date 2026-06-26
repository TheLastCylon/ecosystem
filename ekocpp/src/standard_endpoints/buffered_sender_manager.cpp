#include "buffered_sender_manager.hpp"

namespace {

using SenderRegistry = std::unordered_map<std::string, std::shared_ptr<BufferedSender>>;

nlohmann::json sender_info_json(BufferedSender& sender) {
    return {
        {"route_key", sender.route_key()},
        {"send_process_paused", sender.is_send_process_paused()},
        {"database_sizes", {{"pending", sender.pending_queue_size()}, {"error", sender.error_queue_size()}}},
    };
}

std::shared_ptr<BufferedSender> find_sender(SenderRegistry& registry, const std::string& route_key) {
    auto it = registry.find(route_key);
    return it == registry.end() ? nullptr : it->second;
}

nlohmann::json not_found(const std::string& route_key) {
    return {{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No buffered sender with route key: [" + route_key + "]"}};
}

nlohmann::json with_sender_info(BufferedSender& sender, const std::string& message) {
    return {{"queue_data", sender_info_json(sender)}, {"message", message}};
}

} // namespace

void register_buffered_sender_management_endpoints(RequestRouter& router, SenderRegistry& registry) {
    router.register_endpoint("eco.buffered_sender.data", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               sender    = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};
        return RequestDTO{{
            {"queue_data", sender_info_json(*sender)},
            {"request_data", nullptr},
            {"message", "Buffered Sender[" + route_key + "]: Data retrieved."},
        }};
    });

    router.register_endpoint("eco.buffered_sender.send_process.pause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               sender    = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};
        sender->pause_send_process();
        return RequestDTO{with_sender_info(*sender, "Buffered Sender[" + route_key + "]: Paused SEND PROCESS.")};
    });

    router.register_endpoint("eco.buffered_sender.send_process.unpause", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               sender    = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};
        sender->unpause_send_process();
        return RequestDTO{with_sender_info(*sender, "Buffered Sender[" + route_key + "]: UN-Paused SEND PROCESS.")};
    });

    router.register_endpoint("eco.buffered_sender.errors.get_first_10", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               sender    = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};
        return RequestDTO{{
            {"queue_data", sender->get_first_x_error_span_keys(10)},
            {"message", "Buffered Sender[" + route_key + "]: Retrieved first 10 span-keys for error database."},
        }};
    });

    router.register_endpoint("eco.buffered_sender.errors.reprocess.all", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               sender    = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};
        sender->reprocess_error_queue();
        return RequestDTO{with_sender_info(*sender, "Buffered Sender[" + route_key + "]: Error database entries, moved to Retry database.")};
    });

    router.register_endpoint("eco.buffered_sender.errors.clear", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key = dto.data.at("queue_route_key").get<std::string>();
        auto               sender    = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};
        sender->error_queue_clear();
        return RequestDTO{with_sender_info(*sender, "Buffered Sender[" + route_key + "]: Error database cleared.")};
    });

    router.register_endpoint("eco.buffered_sender.errors.reprocess.one", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key      = dto.data.at("queue_route_key").get<std::string>();
        const std::string span_key_string = dto.data.at("span_key").get<std::string>();
        auto               sender         = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};

        auto result = sender->reprocess_error_queue_span_key(SpanKey::from_string(span_key_string));
        if (!result) {
            return RequestDTO{{{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No request with span-key [" + span_key_string + "] in buffered sender error database, for route key: [" + route_key + "]"}}};
        }
        return RequestDTO{{
            {"queue_data", sender_info_json(*sender)},
            {"request_data", *result},
            {"message", "Buffered Sender[" + route_key + "]: Error database entry[" + span_key_string + "] moved to Retry database."},
        }};
    });

    router.register_endpoint("eco.buffered_sender.errors.pop_request", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key      = dto.data.at("queue_route_key").get<std::string>();
        const std::string span_key_string = dto.data.at("span_key").get<std::string>();
        auto               sender         = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};

        auto result = sender->pop_request_from_error_queue(SpanKey::from_string(span_key_string));
        if (!result) {
            return RequestDTO{{{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No request with span-key [" + span_key_string + "] in buffered sender error database, for route key: [" + route_key + "]"}}};
        }
        return RequestDTO{{
            {"queue_data", sender_info_json(*sender)},
            {"request_data", *result},
            {"message", "Buffered Sender[" + route_key + "]: POPPED Error database entry[" + span_key_string + "]."},
        }};
    });

    router.register_endpoint("eco.buffered_sender.errors.inspect_request", [&registry](SpanKey, RequestDTO& dto) -> RequestDTO {
        const std::string route_key      = dto.data.at("queue_route_key").get<std::string>();
        const std::string span_key_string = dto.data.at("span_key").get<std::string>();
        auto               sender         = find_sender(registry, route_key);
        if (!sender) return RequestDTO{not_found(route_key)};

        auto result = sender->inspect_request_in_error_queue(SpanKey::from_string(span_key_string));
        if (!result) {
            return RequestDTO{{{"queue_data", nullptr}, {"request_data", nullptr}, {"message", "No request with span-key [" + span_key_string + "] in buffered sender error database, for route key: [" + route_key + "]"}}};
        }
        return RequestDTO{{
            {"queue_data", sender_info_json(*sender)},
            {"request_data", *result},
            {"message", "Buffered Sender[" + route_key + "]: INSPECTING Error database entry[" + span_key_string + "]."},
        }};
    });
}
