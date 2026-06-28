cmake_minimum_required(VERSION 3.28)
project(ekocpp_otlp_traces)

set(CMAKE_CXX_STANDARD          20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(nlohmann_json REQUIRED)
find_package(Threads       REQUIRED)
find_package(CURL          REQUIRED)

set(EKOCPP_SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../src)
set(ASIO_INCLUDE   ${CMAKE_CURRENT_SOURCE_DIR}/../third_party/asio/include)

add_library(ekocpp_otlp_traces
    src/otlp_span_exporter.cpp
    src/otlp_tracing_middleware.cpp
    src/otlp_buffered_tracing_middleware.cpp
    src/initiate_otlp_tracing.cpp
)

target_include_directories(ekocpp_otlp_traces
    PUBLIC  src
    PRIVATE ${EKOCPP_SRC_DIR} ${ASIO_INCLUDE}
)

target_link_libraries(ekocpp_otlp_traces
    PUBLIC  nlohmann_json::nlohmann_json
    PRIVATE Threads::Threads CURL::libcurl
)

target_compile_definitions(ekocpp_otlp_traces PUBLIC ASIO_STANDALONE)
