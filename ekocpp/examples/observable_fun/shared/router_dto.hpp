#pragma once
#include <string>
#include <nlohmann/json.hpp>
#include "exceptions/exceptions.hpp"

struct RouterRequestDto {
    std::string    request;
    nlohmann::json to_json()                                 const { return {{"request", request}}; }
    static RouterRequestDto from_json(const nlohmann::json& j)    { return {j.at("request").get<std::string>()}; }
    void validate() const {
        if (request.empty())
            throw ValidationException("request must not be empty");
    }
};

struct RouterResponseDto {
    std::string    response;
    nlohmann::json to_json()                                  const { return {{"response", response}}; }
    static RouterResponseDto from_json(const nlohmann::json& j)    { return {j.at("response").get<std::string>()}; }
    void validate() const {}
};
