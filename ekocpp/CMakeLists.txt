cmake_minimum_required(VERSION 3.28)
project(ekocpp)

set(CMAKE_CXX_STANDARD          20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(nlohmann_json  REQUIRED)
find_package(Threads        REQUIRED)
find_package(spdlog         REQUIRED)
find_package(SQLiteCpp      REQUIRED)

# Vendored, patched asio (third_party/asio_patches/0001-ambient-span-key.patch)
# -- NOT the system package. See documentation/ambient_span_context.md for why:
# native ambient SpanKey propagation across coroutine suspension, woven directly
# into asio::awaitable<T>'s promise (awaitable_frame_base), since asio's own
# await_transform overload set is closed to externally-defined awaitable types.
set(ASIO_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/asio/include)

add_library(ekocpp
        src/data_transfer_objects/span_key.cpp
        src/data_transfer_objects/binary_frame.cpp
    src/servers/server_base.cpp
    src/servers/stream_server_base.cpp
    src/servers/tcp_server.cpp
    src/servers/uds_server.cpp
    src/servers/udp_server.cpp
    src/clients/client_base.cpp
    src/clients/stream_client_base.cpp
    src/clients/persistent_stream_client_base.cpp
    src/clients/udp_client.cpp
    src/clients/transient_tcp_client.cpp
    src/clients/transient_uds_client.cpp
    src/clients/persisted_tcp_client.cpp
    src/clients/persisted_uds_client.cpp
    src/configuration/argument_parser.cpp
    src/configuration/config_models.cpp
    src/coroutines/ambient_span_context.cpp
    src/logs/eco_logger.cpp
    src/logs/otlp_formatter.cpp
    src/state_keepers/statistics_keeper.cpp
    src/state_keepers/error_state_list.cpp
    src/standard_endpoints/errors.cpp
    src/standard_endpoints/statistics.cpp
    src/standard_endpoints/log_manager.cpp
    src/standard_endpoints/buffered_handler_manager.cpp
    src/standard_endpoints/buffered_sender_manager.cpp
    src/application_base.cpp
)
target_include_directories(ekocpp PUBLIC src ${ASIO_INCLUDE_DIRS})
target_link_libraries(ekocpp PUBLIC nlohmann_json::nlohmann_json Threads::Threads spdlog::spdlog SQLiteCpp)
target_compile_definitions(ekocpp PUBLIC ASIO_STANDALONE)

add_executable(ekocpp_server src/main.cpp)
target_link_libraries(ekocpp_server PRIVATE ekocpp)

add_executable(queue_smoke_test tests/queue_smoke_test.cpp)
target_link_libraries(queue_smoke_test PRIVATE ekocpp)

add_executable(statistics_keeper_smoke_test tests/statistics_keeper_smoke_test.cpp)
target_link_libraries(statistics_keeper_smoke_test PRIVATE ekocpp)

add_executable(buffered_request_handler_smoke_test tests/buffered_request_handler_smoke_test.cpp)
target_link_libraries(buffered_request_handler_smoke_test PRIVATE ekocpp)

add_executable(application_base_buffered_endpoint_live_test tests/application_base_buffered_endpoint_live_test.cpp)
target_link_libraries(application_base_buffered_endpoint_live_test PRIVATE ekocpp)

add_executable(buffered_sender_smoke_test tests/buffered_sender_smoke_test.cpp)
target_link_libraries(buffered_sender_smoke_test PRIVATE ekocpp)

add_executable(standard_endpoints_phase1to3_live_test tests/standard_endpoints_phase1to3_live_test.cpp)
target_link_libraries(standard_endpoints_phase1to3_live_test PRIVATE ekocpp)

add_executable(standard_endpoints_buffered_management_live_test tests/standard_endpoints_buffered_management_live_test.cpp)
target_link_libraries(standard_endpoints_buffered_management_live_test PRIVATE ekocpp)

add_executable(request_router_exception_smoke_test tests/request_router_exception_smoke_test.cpp)
target_link_libraries(request_router_exception_smoke_test PRIVATE ekocpp)

add_executable(fire_and_forget_smoke_test tests/fire_and_forget_smoke_test.cpp)
target_link_libraries(fire_and_forget_smoke_test PRIVATE ekocpp)

add_executable(lru_cache_smoke_test tests/lru_cache_smoke_test.cpp)
target_link_libraries(lru_cache_smoke_test PRIVATE ekocpp)

add_executable(json_dto_smoke_test tests/json_dto_smoke_test.cpp)
target_link_libraries(json_dto_smoke_test PRIVATE ekocpp)

add_executable(middleware_smoke_test tests/middleware_smoke_test.cpp)
target_link_libraries(middleware_smoke_test PRIVATE ekocpp)

add_subdirectory(otlp_traces)
add_subdirectory(otlp_metrics)
add_subdirectory(examples/observable_fun)
