#pragma once

#include <functional>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <utility>

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/json_dto.hpp"
#include "../exceptions/exceptions.hpp"
#include "../middleware/middleware_manager.hpp"
#include "../state_keepers/statistics_keeper.hpp"
#include "function_traits.hpp"
#include "request_context.hpp"
#include "status.hpp"

// The injectable-type registry: resolve<T>() maps a handler parameter type
// to its value at dispatch time. Three cases:
//   SpanKey    -- injected directly from the request context
//   RequestDTO& -- raw inbound DTO, for handlers that do their own parsing
//   JsonDTO T  -- framework deserialises from_json(), then calls validate();
//                 nlohmann structural errors are caught and re-thrown as
//                 ValidationException (status 300) rather than surfacing as
//                 UNHANDLED (status 999). Unsupported types are a compile error.
template <typename T>
T resolve(RequestContext& request_context) {
    if constexpr (std::is_same_v<T, SpanKey>) {
        return request_context.span_key;
    } else if constexpr (std::is_same_v<T, RequestDTO&>) {
        return request_context.dto;
    } else {
        static_assert(JsonDTO<T>,
            "Handler parameter must be SpanKey, RequestDTO&, or a type satisfying JsonDTO "
            "(implement to_json(), static from_json(), and validate()).");
        try {
            T dto = T::from_json(request_context.dto.data);
            dto.validate();
            return dto;
        } catch (const ValidationException&) {
            throw;
        } catch (const nlohmann::json::exception& e) {
            throw ValidationException(std::string("DTO deserialisation failed: ") + e.what());
        }
    }
}

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

// HandlerWrapper always returns the "data" portion of a response as JSON,
// wrapped in a coroutine so any handler -- sync or async -- can be awaited
// uniformly by dispatch(). Sync handlers become trivial coroutines that
// co_return immediately; async handlers co_await their own awaitable.
using HandlerWrapper = std::function<asio::awaitable<nlohmann::json>(RequestContext&)>;

// make_handler_wrapper normalises any handler into the HandlerWrapper shape.
// Two compile-time paths:
//   Async handler  -- returns asio::awaitable<T> where T satisfies JsonDTO;
//                     co_awaits the awaitable, calls .to_json() on the result.
//   Sync handler   -- returns T directly where T satisfies JsonDTO;
//                     calls synchronously, co_returns .to_json().
// void handlers are gone: use EmptyDto for handlers that have nothing to return.
template <typename Handler>
HandlerWrapper make_handler_wrapper(Handler handler) {
    using traits      = function_traits<Handler>;
    using return_type = typename traits::return_type;

    if constexpr (is_awaitable<return_type>::value) {
        using value_type = typename is_awaitable<return_type>::value_type;
        static_assert(JsonDTO<value_type>,
            "Coroutine handler return type T in asio::awaitable<T> must satisfy JsonDTO "
            "(implement to_json() const and static from_json(const nlohmann::json&)).");
        return [handler](RequestContext& rc) -> asio::awaitable<nlohmann::json> {
            auto result = co_await invoke_with_context(
                handler, rc, std::make_index_sequence<traits::argument_type_list_size>{}
            );
            co_return result.to_json();
        };
    } else {
        static_assert(JsonDTO<return_type>,
            "Handler return type must satisfy JsonDTO "
            "(implement to_json() const and static from_json(const nlohmann::json&)). "
            "Use EmptyDto for handlers with no meaningful return value.");
        return [handler](RequestContext& rc) -> asio::awaitable<nlohmann::json> {
            co_return invoke_with_context(
                handler, rc, std::make_index_sequence<traits::argument_type_list_size>{}
            ).to_json();
        };
    }
}

// Route table: type-erases every registered handler behind HandlerWrapper so
// handlers of different signatures can live in the same container. The
// compile-time resolution machinery runs once, inside make_handler_wrapper,
// at registration time -- dispatch() itself is a plain runtime lookup+co_await.
//
// Response envelope mirrors the Python ekosis ResponseDTO shape esnc already
// decodes: {"status": int, "data": ...}.
class RequestRouter {
public:
    template <typename Handler>
    void register_endpoint(std::string route_key, Handler handler) {
        StatisticsKeeper::instance().track_endpoint_data(route_key);
        route_table_[std::move(route_key)] = make_handler_wrapper(handler);
    }

    // Member function overload: binds instance + method into a callable and
    // forwards to the single-handler overload. The generated lambda is a
    // one-liner (not itself a coroutine), so coroutine member functions
    // (returning asio::awaitable<T>) also work without triggering the GCC 13 ICE.
    template <typename ClassType, typename ReturnType, typename... Args>
    void register_endpoint(std::string route_key, ClassType* instance, ReturnType (ClassType::*method)(Args...)) {
        register_endpoint(std::move(route_key), [instance, method](Args... args) -> ReturnType {
            return (instance->*method)(std::forward<Args>(args)...);
        });
    }

    // For registering a handler that already matches HandlerWrapper's shape
    // directly (RequestContext& -> asio::awaitable<json>), bypassing
    // make_handler_wrapper's function_traits-based call generation --
    // BufferedRequestHandler::push is the first such case.
    void register_raw_handler(std::string route_key, HandlerWrapper wrapper) {
        StatisticsKeeper::instance().track_endpoint_data(route_key);
        route_table_[std::move(route_key)] = std::move(wrapper);
    }

    // Mirrors request_router.py's route_request: an unknown route_key maps
    // straight to ROUTE_KEY_UNKNOWN (Python raises UnknownRouteKeyException
    // immediately, never entering the try block at all -- same here, no
    // handler call is attempted). ApplicationProcessingException is the one
    // exception type dispatch() itself catches and maps to a status.
    // Anything else a handler throws propagates to ServerBase::route_request.
    asio::awaitable<nlohmann::json> dispatch(const std::string& route_key, RequestContext& request_context) const {
        auto it = route_table_.find(route_key);
        if (it == route_table_.end()) {
            co_return nlohmann::json{
                {"status", static_cast<int>(Status::ROUTE_KEY_UNKNOWN)},
                {"data",   "Unknown route key '" + route_key + "'"}
            };
        }
        try {
            auto& mm = MiddlewareManager::instance();
            RequestDTO processed_dto = co_await mm.run_before_routing(request_context.span_key, request_context.dto);
            RequestContext middleware_context{request_context.span_key, processed_dto};
            nlohmann::json data   = co_await it->second(middleware_context);
            nlohmann::json result = co_await mm.run_after_routing(request_context.span_key, std::move(data));
            co_return nlohmann::json{
                {"status", static_cast<int>(Status::SUCCESS)},
                {"data",   result}
            };
        } catch (const ApplicationProcessingException& e) {
            co_return nlohmann::json{
                {"status", static_cast<int>(Status::PROCESSING_FAILURE)},
                {"data",   "Processing Failure '" + route_key + "', message: '" + std::string(e.what()) + "'"}
            };
        }
    }

private:
    std::unordered_map<std::string, HandlerWrapper> route_table_;
};
