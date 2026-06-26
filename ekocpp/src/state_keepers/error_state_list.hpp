#pragma once

#include <string>
#include <unordered_map>
#include <vector>

#include <nlohmann/json.hpp>

#include "error_state_keeper.hpp"

// Mirrors ekosis/state_keepers/error_state_list.py's ErrorStateList. Plain
// Meyers singleton, same reasoning as StatisticsKeeper -- no construction
// arguments needed.
class ErrorStateList {
public:
    static ErrorStateList& instance();

    bool has_error_id(const std::string& error_id) const;
    void increment(const std::string& error_id, const std::string& description);
    void clear_some(const std::string& error_id, int how_many);
    void clear_all(const std::string& error_id);

    // Only the error_ids currently is_set() (count > 0) -- matches Python's
    // get_error_states() filtering.
    std::vector<nlohmann::json> get_error_states_json() const;

private:
    ErrorStateList() = default;

    std::unordered_map<std::string, ErrorStateKeeper> error_state_map_;
};
