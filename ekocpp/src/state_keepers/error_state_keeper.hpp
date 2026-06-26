#pragma once

#include <string>

#include <nlohmann/json.hpp>

// Mirrors ekosis/state_keepers/error_state_keeper.py's ErrorStateKeeper -- a
// single named error counter. No to_json() formal DTO needed (unlike
// Python's to_dict()) -- ekocpp handlers already return plain json directly.
class ErrorStateKeeper {
public:
    ErrorStateKeeper(std::string error_id, std::string description)
        : error_id_(std::move(error_id)), description_(std::move(description)) {}

    void increment() { ++error_count_; }
    void clear_some(int how_many) { error_count_ = error_count_ >= how_many ? error_count_ - how_many : 0; }
    void clear_all() { error_count_ = 0; }

    int error_count() const { return error_count_; }
    bool is_set() const { return error_count_ > 0; }
    const std::string& error_id() const { return error_id_; }
    const std::string& description() const { return description_; }

    nlohmann::json to_json() const {
        return {{"error_id", error_id_}, {"description", description_}, {"count", error_count_}};
    }

private:
    std::string error_id_;
    std::string description_;
    int         error_count_ = 0;
};
