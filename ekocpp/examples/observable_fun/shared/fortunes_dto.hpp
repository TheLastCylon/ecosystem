#pragma once
#include <string>
#include <nlohmann/json.hpp>

struct FortuneResponseDto {
    std::string    fortune;
    nlohmann::json to_json()                                  const { return {{"fortune", fortune}}; }
    static FortuneResponseDto from_json(const nlohmann::json& j)    { return {j.at("fortune").get<std::string>()}; }
    void validate() const {}
};
