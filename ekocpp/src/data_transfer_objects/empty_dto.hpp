#pragma once

#include <nlohmann/json.hpp>

// Mirrors ekosis/data_transfer_objects/empty.py's EmptyDto -- a concrete DTO
// that carries no payload. Handlers with nothing meaningful to return declare
// EmptyDto (or asio::awaitable<EmptyDto>) instead of void, satisfying JsonDto
// the same way every other DTO does.
struct EmptyDto {
    static EmptyDto    from_json(const nlohmann::json&) { return {}; }
    nlohmann::json     to_json()                  const { return nlohmann::json::object(); }
};
