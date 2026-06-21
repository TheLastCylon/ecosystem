# function_traits -- compile-time handler introspection

**Status:** decided, 2026-06-21. Not yet implemented in source -- this is the design lock.

## Problem

Python's `ekosis` filters kwargs down to a handler's declared parameters at
runtime, via `inspect.signature(function).parameters` captured once at
decoration time (`endpoint.py`/`buffered_endpoint.py`). For `ekocpp` we want
the C++ equivalent done at compile time instead: a handler declares only the
parameters it actually uses (`SpanKey`, `RequestDTO&`, or both, in any order),
and `register_endpoint` builds the correct call with zero runtime dispatch.

## Mechanism: recursive structural pattern-matching on callable type-shapes

Each specialization below is a grammar production over "the shape of a
callable type." Resolution is the compiler walking those productions,
recursing via inheritance, until it lands on the one base case that actually
has a body (`Ret(Args...)`). Not lexical analysis -- closer to a parser whose
language is C++ callable type-shapes.

```cpp
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
```

- **Primary template** (no longer just a forward declaration) is the fallback
  case: "whatever T is, go look at the type of its `operator()` instead."
  Only fires for lambdas/functors -- specializations are tried first, most
  specific match wins, so a bare function type or function pointer never
  falls through to this.
- **Free function type** (`Ret(Args...)`) is the canonical/base case. Every
  other specialization inherits from this one rather than duplicating its
  body -- single source of truth, add a member once, every specialization
  gets it for free.
- **Function pointer** (`Ret(*)(Args...)`) -- needed because passing a free
  function as an argument decays it to a pointer type, which would otherwise
  fail to match the canonical specialization at all.
- **Member-function-pointer, const and non-const** -- needed because a
  lambda's `&T::operator()` is a pointer-to-member-function, not a plain
  function pointer. `const` covers ordinary lambdas (default,
  non-`mutable`); the non-const overload covers `mutable` lambdas.
  `const` here means "doesn't modify the lambda's own captures," nothing
  to do with the parameter types themselves.
- **Known gap, not pursued:** generic lambdas (`[](auto x){}`) don't resolve
  via this mechanism -- their `operator()` is itself a template, so
  `&T::operator()` has no single concrete type to decltype. Not needed for
  day-one handlers (plain functions / non-generic lambdas only).

## Usage: RequestContext resolution

```cpp
struct RequestContext {
    SpanKey      span_key;
    RequestDTO&  dto;
};

template <typename T> T resolve(RequestContext& request_context);

template <> SpanKey     resolve<SpanKey>    (RequestContext& request_context) { return request_context.span_key; }
template <> RequestDTO& resolve<RequestDTO&>(RequestContext& request_context) { return request_context.dto; }

template <typename Handler, size_t... IndexSequence>
void invoke_with_context(Handler handler, RequestContext& request_context, std::index_sequence<IndexSequence...>) {
    using traits = function_traits<Handler>;
    handler(
        resolve<
            typename traits::template argument_type_at<
                IndexSequence
            >
        >(request_context)...
    );
}

template <typename Handler>
void register_endpoint(Handler handler, RequestContext& request_context) {
    using traits = function_traits<Handler>;
    invoke_with_context(
        handler,
        request_context,
        std::make_index_sequence<traits::argument_type_list_size>{}
    );
}
```

`std::make_index_sequence<N>` is the compile-time stand-in for a loop counter
-- `std::index_sequence<0, 1, ...>` exists purely to get those integers into
a position where `IndexSequence...` can pack-expand them, one resolved
argument per position, fanned straight into the call to `handler`.

`SpanKey` resolves by value (24 bytes, trivially copyable, an identity
snapshot -- copying it is cheaper than the indirection a reference would
cost, and copying signals "yours now, immutable"). `RequestDTO` resolves by
reference (the actual payload -- one object, handlers borrow it, nobody
duplicates it).

**`RequestContext`**, not `EndpointContext` -- the same resolve-by-type
mechanism is expected to extend to buffered/queued handlers later, not just
standard endpoints, and "per-request data" reads correctly in both cases.

## Adding a new injectable type later

Add one `resolve<NewType>` specialization. Nothing else in the mechanism
changes -- this is the registry `register_endpoint` was designed around.

## A note on power and responsibility

This is genuinely the on-ramp to compile-time Turing-completeness via
recursive template specialization -- the same family of trick that produces
compile-time Brainfuck interpreters and four-minute single-binary builds
when taken too far. Use it for what it's here for (handler parameter
resolution), not because it's fun to watch the compiler sweat.

Also: cats should not be allowed near this code. Footprints in cement are
permanent, and a stray paw on the keyboard mid-template-instantiation is a
compile error nobody will ever be able to explain to Buddy Hamilton.
