#pragma once

#include <concepts>

#include <nlohmann/json.hpp>

// Compile-time contract for any type that crosses the ekocpp wire as a DTO.
// Three requirements -- all DTOs, inbound and outbound, satisfy all three:
//   to_json()   -- serialise to wire format
//   from_json() -- deserialise from wire format
//   validate()  -- assert semantic constraints; throw ValidationException on
//                  failure. Outbound DTOs implement it as a no-op. Inbound
//                  DTOs use it to enforce field-level business rules. The
//                  compiler enforces the contract; developer discipline does not.
//
// Deliberately a concept rather than a base class: existing DTOs are plain
// aggregates with no inheritance, and a concept gives the same compile-time
// enforcement with a clean diagnostic instead of template-error spew.
template <typename T>
concept JsonDTO = requires(const T& value, const nlohmann::json& j) {
    { value.to_json()  } -> std::convertible_to<nlohmann::json>;
    { T::from_json(j)  } -> std::same_as<T>;
    { value.validate() } -> std::same_as<void>;
};
