#include "error_state_list.hpp"

#include <algorithm>

namespace {

std::string to_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return std::toupper(c); });
    return s;
}

} // namespace

ErrorStateList& ErrorStateList::instance() {
    static ErrorStateList list;
    return list;
}

bool ErrorStateList::has_error_id(const std::string& error_id) const {
    return error_state_map_.find(to_upper(error_id)) != error_state_map_.end();
}

void ErrorStateList::increment(const std::string& error_id, const std::string& description) {
    const std::string error_id_upper = to_upper(error_id);
    auto it = error_state_map_.find(error_id_upper);
    if (it == error_state_map_.end()) {
        it = error_state_map_.emplace(error_id_upper, ErrorStateKeeper(error_id_upper, description)).first;
    }
    it->second.increment();
}

void ErrorStateList::clear_some(const std::string& error_id, int how_many) {
    auto it = error_state_map_.find(to_upper(error_id));
    if (it != error_state_map_.end()) {
        it->second.clear_some(how_many);
    }
}

void ErrorStateList::clear_all(const std::string& error_id) {
    auto it = error_state_map_.find(to_upper(error_id));
    if (it != error_state_map_.end()) {
        it->second.clear_all();
    }
}

std::vector<nlohmann::json> ErrorStateList::get_error_states_json() const {
    std::vector<nlohmann::json> result;
    for (const auto& [key, error_state] : error_state_map_) {
        if (error_state.is_set()) {
            result.push_back(error_state.to_json());
        }
    }
    return result;
}
