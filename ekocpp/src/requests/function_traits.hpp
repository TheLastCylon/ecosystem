#pragma once

#include <cstddef>
#include <tuple>
#include <type_traits>

#include <asio/awaitable.hpp>

// Recursive structural pattern-matching on callable type-shapes. See
// ekocpp/documentation/function_traits.md for the full design rationale --
// this is the implementation of that decision, unchanged from the doc.

template <typename T>
struct function_traits : function_traits<decltype(&T::operator())> {};

template <typename ReturnType, typename... ArgumentTypeList>
struct function_traits<ReturnType(ArgumentTypeList...)> {
    using                   return_type             = ReturnType;
    static constexpr size_t argument_type_list_size = sizeof...(ArgumentTypeList);

    template <size_t N>
    using argument_type_at = std::tuple_element_t<N, std::tuple<ArgumentTypeList...>>;
};

template <typename ReturnType, typename... ArgumentTypeList>
struct function_traits<ReturnType(*)(ArgumentTypeList...)>
    : function_traits<ReturnType(ArgumentTypeList...)> {};

template <typename ClassType, typename ReturnType, typename... ArgumentTypeList>
struct function_traits<ReturnType (ClassType::*)(ArgumentTypeList...) const>
    : function_traits<ReturnType(ArgumentTypeList...)> {};

template <typename ClassType, typename ReturnType, typename... ArgumentTypeList>
struct function_traits<ReturnType (ClassType::*)(ArgumentTypeList...)>
    : function_traits<ReturnType(ArgumentTypeList...)> {};

// Detects whether T is asio::awaitable<U>. Used in make_handler_wrapper and
// the buffered-handler processing loop to branch at compile time between sync
// handlers (call directly, co_return the result) and coroutine handlers
// (co_await the returned awaitable).
template <typename T>          struct is_awaitable              : std::false_type {};
template <typename T>          struct is_awaitable<asio::awaitable<T>> : std::true_type  { using value_type = T; };
