cmake_minimum_required(VERSION 3.28)
project(ekosis_log_shipper)

set(CMAKE_CXX_STANDARD          20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SQLITE3   REQUIRED sqlite3)
pkg_check_modules(LIBCURL   REQUIRED libcurl)
find_package(nlohmann_json  REQUIRED)
find_package(SQLiteCpp      REQUIRED)

add_library(ekosis_log_shipper_lib
    src/tracked_file.cpp
    src/state_store.cpp
    src/otlp_envelope.cpp
    src/http_sender.cpp
)
target_include_directories(ekosis_log_shipper_lib PUBLIC src)
target_link_libraries(ekosis_log_shipper_lib PUBLIC
    SQLiteCpp
    nlohmann_json::nlohmann_json
    ${LIBCURL_LIBRARIES}
)
target_include_directories(ekosis_log_shipper_lib PUBLIC ${LIBCURL_INCLUDE_DIRS})

add_executable(ekosis_log_shipper src/main.cpp)
target_link_libraries(ekosis_log_shipper PRIVATE ekosis_log_shipper_lib)

enable_testing()
add_subdirectory(tests)
