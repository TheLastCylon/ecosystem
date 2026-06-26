#include <cstdio>

#include <nlohmann/json.hpp>

#include "../src/data_transfer_objects/empty_dto.hpp"
#include "../src/data_transfer_objects/request_dto.hpp"
#include "../src/data_transfer_objects/response_dto.hpp"
#include "../src/data_transfer_objects/span_key.hpp"
#include "../src/data_transfer_objects/json_dto.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

// --- Positive: all three concrete DTOs must satisfy JsonDto --------------
static_assert(JsonDTO<EmptyDto>,    "EmptyDto must satisfy JsonDto");
static_assert(JsonDTO<RequestDTO>,  "RequestDTO must satisfy JsonDto");
static_assert(JsonDTO<ResponseDTO>, "ResponseDTO must satisfy JsonDto");
static_assert(JsonDTO<SpanKey>,     "SpanKey must satisfy JsonDto");

// --- Negative: missing either method fails the concept -------------------
struct MissingFromJson {
    nlohmann::json to_json() const { return {}; }
};
static_assert(!JsonDTO<MissingFromJson>, "MissingFromJson must NOT satisfy JsonDto");

struct MissingToJson {
    static MissingToJson from_json(const nlohmann::json&) { return {}; }
};
static_assert(!JsonDTO<MissingToJson>, "MissingToJson must NOT satisfy JsonDto");

} // namespace

int main() {
    // --- EmptyDto round-trip -----------------------------------------------
    const EmptyDto original_empty;
    const auto     empty_json = original_empty.to_json();
    check(empty_json.is_object(), "EmptyDto::to_json() returns a JSON object");
    check(empty_json.empty(),     "EmptyDto::to_json() returns an empty JSON object");
    check(EmptyDto::from_json(empty_json).to_json() == empty_json,
          "EmptyDto round-trips to the same JSON");
    check(EmptyDto::from_json({{"irrelevant", 42}}).to_json().empty(),
          "EmptyDto::from_json ignores its argument");

    // --- RequestDTO round-trip ---------------------------------------------
    const RequestDTO original_req{{{"key", "value"}, {"n", 42}}};
    const auto       req_json = original_req.to_json();
    check(req_json["key"] == "value", "RequestDTO::to_json() preserves data fields");
    check(req_json["n"]   == 42,      "RequestDTO::to_json() preserves numeric field");
    const RequestDTO restored_req = RequestDTO::from_json(req_json);
    check(restored_req.to_json() == req_json, "RequestDTO round-trips to the same JSON");

    // --- ResponseDTO round-trip --------------------------------------------
    // to_json() omits span_key (wire format); from_json() produces default span_key.
    const SpanKey     sk   = SpanKey::generate();
    const ResponseDTO original_resp{sk, 200, {{"result", "ok"}}};
    const auto        resp_json = original_resp.to_json();
    check(resp_json.contains("status"),      "ResponseDTO::to_json() has status");
    check(resp_json.contains("data"),        "ResponseDTO::to_json() has data");
    check(!resp_json.contains("span_key"),   "ResponseDTO::to_json() omits span_key (wire format)");
    check(resp_json["status"] == 200,        "ResponseDTO::to_json() status == 200");
    check(resp_json["data"]["result"] == "ok", "ResponseDTO::to_json() data correct");

    const ResponseDTO restored_resp = ResponseDTO::from_json(resp_json);
    check(restored_resp.status           == 200,  "ResponseDTO::from_json() restores status");
    check(restored_resp.data["result"]   == "ok", "ResponseDTO::from_json() restores data");
    check(restored_resp.span_key         == SpanKey{},
          "ResponseDTO::from_json() produces default span_key (populated externally)");

    std::printf("\nAll JsonDto smoke tests passed.\n");
    return 0;
}
