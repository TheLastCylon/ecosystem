cmake_minimum_required(VERSION 3.28)
project(ekosis_net_cat)

set(CMAKE_CXX_STANDARD          20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(ASIO      REQUIRED asio)
find_package(nlohmann_json  REQUIRED)

add_library(ekosis_net_cat_lib
    src/span_key.cpp
    src/binary_frame.cpp
    src/tcp_client.cpp
    src/udp_client.cpp
    src/uds_client.cpp
)
target_include_directories(ekosis_net_cat_lib PUBLIC src ${ASIO_INCLUDE_DIRS})
target_link_libraries(ekosis_net_cat_lib PUBLIC nlohmann_json::nlohmann_json)
target_compile_definitions(ekosis_net_cat_lib PUBLIC ASIO_STANDALONE)

add_executable(esnc src/main.cpp)
target_link_libraries(esnc PRIVATE ekosis_net_cat_lib)

enable_testing()
add_subdirectory(tests)
