#pragma once
#include <string>
#include <nlohmann/json.hpp>
#include "exceptions/exceptions.hpp"

struct TrackerLogRequestDto {
    std::string request;
    double      timestamp;
    nlohmann::json to_json()                                      const { return {{"request", request}, {"timestamp", timestamp}}; }
    static TrackerLogRequestDto from_json(const nlohmann::json& j)      { return {j.at("request").get<std::string>(), j.at("timestamp").get<double>()}; }
    void validate() const {
        if (request.empty())
            throw ValidationException("request must not be empty");
        if (timestamp <= 0.0)
            throw ValidationException("timestamp must be a positive unix epoch value");
    }
};
