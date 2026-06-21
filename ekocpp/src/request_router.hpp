#pragma once

#include <functional>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <utility>

#include <nlohmann/json.hpp>

#include "function_traits.hpp"
#include "request_context.hpp"

// The injectable-type registry: add one specialization here per type a
// handler is allowed to ask for. Nothing else in the mechanism changes.
template <typename T> T resolve(RequestContext& request_context);

template <> inline SpanKey     resolve<SpanKey>    (RequestContext& request_context) { return request_context.span_key; }
template <> inline RequestDTO& resolve<RequestDTO&>(RequestContext& request_context) { return request_context.dto; }

template <typename Handler, size_t... IndexSequence>
auto invoke_with_context(Handler handler, RequestContext& request_context, std::index_sequence<IndexSequence...>) {
    using traits = function_traits<Handler>;
    return handler(
        resolve<
            typename traits::template argument_type_at<
                IndexSequence
            >
        >(request_context)...
    );
}

// HandlerWrapper always returns the "data" portion of a response, as JSON --
// void handlers (fire-and-forget) report back null. Status/envelope shape is
// RequestRouter::dispatch's job, not the wrapper's.
using HandlerWrapper = std::function<nlohmann::json(RequestContext&)>;

template <typename Handler>
HandlerWrapper make_handler_wrapper(Handler handler) {
    return [handler](RequestContext& request_context) -> nlohmann::json {
        using traits = function_traits<Handler>;
        if constexpr (std::is_void_v<typename traits::return_type>) {
            invoke_with_context(handler, request_context, std::make_index_sequence<traits::argument_type_list_size>{});
            return nullptr;
        } else {
            return invoke_with_context(handler, request_context, std::make_index_sequence<traits::argument_type_list_size>{});
        }
    };
}

// Route table: type-erases every registered handler behind HandlerWrapper so
// handlers of different signatures can live in the same container. The
// compile-time resolution machinery runs once, inside make_handler_wrapper,
// at registration time -- dispatch() itself is a plain runtime lookup+call.
//
// Response envelope mirrors the Python ekosis ResponseDTO shape esnc already
// decodes: {"status": int, "data": ...}. status 400 == ROUTE_KEY_UNKNOWN.
class RequestRouter {
public:
    template <typename Handler>
    void register_endpoint(std::string route_key, Handler handler) {
        route_table_[std::move(route_key)] = make_handler_wrapper(handler);
    }

    nlohmann::json dispatch(const std::string& route_key, RequestContext& request_context) const {
        auto it = route_table_.find(route_key);
        if (it == route_table_.end()) {
            return { {"status", 400}, {"data", nullptr} };
        }
        return { {"status", 0}, {"data", it->second(request_context)} };
    }

private:
    std::unordered_map<std::string, HandlerWrapper> route_table_;
};
