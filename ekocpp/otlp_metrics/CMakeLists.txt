cmake_minimum_required(VERSION 3.28)
project(ekocpp_otlp_metrics)

set(CMAKE_CXX_STANDARD          20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(nlohmann_json REQUIRED)
find_package(Threads       REQUIRED)
find_package(CURL          REQUIRED)
find_package(spdlog        REQUIRED)

set(EKOCPP_SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../src)
set(ASIO_INCLUDE   ${CMAKE_CURRENT_SOURCE_DIR}/../third_party/asio/include)

add_executable(ekocpp_otlp_metrics
    src/service_discovery.cpp
    src/stats_translator.cpp
    src/otlp_metrics_exporter.cpp
    src/metrics_scraper.cpp
    src/main.cpp
)

target_include_directories(ekocpp_otlp_metrics PRIVATE
    src
    ${EKOCPP_SRC_DIR}
    ${ASIO_INCLUDE}
)

target_link_libraries(ekocpp_otlp_metrics PRIVATE
    ekocpp
    CURL::libcurl
)

target_compile_definitions(ekocpp_otlp_metrics PRIVATE ASIO_STANDALONE)
