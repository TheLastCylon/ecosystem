#pragma once

#include <cstddef>
#include <tuple>

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
