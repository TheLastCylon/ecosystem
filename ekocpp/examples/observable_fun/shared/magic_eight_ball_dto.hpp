#pragma once
#include <string>
#include <nlohmann/json.hpp>

struct Magic8BallResponseDto {
    std::string    prediction;
    nlohmann::json to_json()                                    const { return {{"prediction", prediction}}; }
    static Magic8BallResponseDto from_json(const nlohmann::json& j)   { return {j.at("prediction").get<std::string>()}; }
    void validate() const {}
};
