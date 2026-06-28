#pragma once
#include <string>
#include <nlohmann/json.hpp>

struct CurrentTimeResponseDto {
    std::string    time;
    nlohmann::json to_json()                                    const { return {{"time", time}}; }
    static CurrentTimeResponseDto from_json(const nlohmann::json& j) { return {j.at("time").get<std::string>()}; }
    void validate() const {}
};
