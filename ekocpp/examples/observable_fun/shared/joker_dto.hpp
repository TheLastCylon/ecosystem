#pragma once
#include <string>
#include <nlohmann/json.hpp>

struct JokerResponseDto {
    std::string    joke;
    nlohmann::json to_json()                               const { return {{"joke", joke}}; }
    static JokerResponseDto from_json(const nlohmann::json& j)   { return {j.at("joke").get<std::string>()}; }
    void validate() const {}
};
