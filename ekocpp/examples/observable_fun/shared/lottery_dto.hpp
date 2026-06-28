#pragma once
#include <string>
#include <vector>
#include <nlohmann/json.hpp>
#include "exceptions/exceptions.hpp"

struct NumberPickerRequestDto {
    int            how_many = 1;
    nlohmann::json to_json()                                        const { return {{"how_many", how_many}}; }
    static NumberPickerRequestDto from_json(const nlohmann::json& j)      { return {j.at("how_many").get<int>()}; }
    void validate() const {
        if (how_many < 1)
            throw ValidationException("how_many must be at least 1");
    }
};

struct NumberPickerResponseDto {
    std::vector<std::string> numbers;
    nlohmann::json to_json() const { nlohmann::json j; j["numbers"] = numbers; return j; }
    static NumberPickerResponseDto from_json(const nlohmann::json& j) {
        return {j.at("numbers").get<std::vector<std::string>>()};
    }
    void validate() const {}
};
