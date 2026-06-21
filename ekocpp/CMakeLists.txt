cmake_minimum_required(VERSION 3.28)
project(ekocpp)

set(CMAKE_CXX_STANDARD          20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(ASIO      REQUIRED asio)
find_package(nlohmann_json  REQUIRED)
find_package(Threads        REQUIRED)

add_library(ekocpp_lib
    src/span_key.cpp
    src/binary_frame.cpp
    src/connection_handler.cpp
)
target_include_directories(ekocpp_lib PUBLIC src ${ASIO_INCLUDE_DIRS})
target_link_libraries(ekocpp_lib PUBLIC nlohmann_json::nlohmann_json Threads::Threads)
target_compile_definitions(ekocpp_lib PUBLIC ASIO_STANDALONE)

add_executable(ekocpp_server src/main.cpp)
target_link_libraries(ekocpp_server PRIVATE ekocpp_lib)
