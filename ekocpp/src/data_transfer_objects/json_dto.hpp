#pragma once

#include <concepts>

#include <nlohmann/json.hpp>

// Compile-time contract for any type that crosses the ekocpp wire as a DTO.
// Mirrors the structural guarantee Pydantic's BaseModel provides in Python:
// a DTO can be serialised to JSON and deserialised from JSON.
//
// Both directions are required -- a type that only goes out is a one-way
// emission format (OtlpLogRecord is the canonical example), not a DTO.
//
// Deliberately a concept rather than a base class: existing DTOs are plain
// aggregates with no inheritance, and a concept gives the same compile-time
// enforcement with a clean diagnostic instead of template-error spew.
template <typename T>
concept JsonDTO = requires(const T& value, const nlohmann::json& j) {
    { value.to_json()  } -> std::convertible_to<nlohmann::json>;
    { T::from_json(j)  } -> std::same_as<T>;
};
