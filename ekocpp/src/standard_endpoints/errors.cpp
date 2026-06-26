#include "errors.hpp"

#include "../state_keepers/error_state_list.hpp"

namespace {

nlohmann::json build_errors_response() {
    nlohmann::json errors = nlohmann::json::array();
    for (auto& error_state : ErrorStateList::instance().get_error_states_json()) {
        errors.push_back(std::move(error_state));
    }
    return {{"errors", errors}};
}

RequestDTO eco_error_states_get(SpanKey, RequestDTO&) {
    return RequestDTO{build_errors_response()};
}

RequestDTO eco_error_states_clear(SpanKey, RequestDTO& dto) {
    const std::string error_id = dto.data.at("error_id").get<std::string>();
    const int          count    = dto.data.value("count", 0);

    if (ErrorStateList::instance().has_error_id(error_id)) {
        if (count == 0) {
            ErrorStateList::instance().clear_all(error_id);
        } else {
            ErrorStateList::instance().clear_some(error_id, count);
        }
    }
    return RequestDTO{build_errors_response()};
}

} // namespace

void register_error_endpoints(RequestRouter& router) {
    router.register_endpoint("eco.error_states.get", eco_error_states_get);
    router.register_endpoint("eco.error_states.clear", eco_error_states_clear);
}
