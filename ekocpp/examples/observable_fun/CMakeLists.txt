cmake_minimum_required(VERSION 3.28)

# Each service is its own executable. OUTPUT_NAME matches the service name so
# env var lookup stays clean (ECOENV_UDP_FORTUNES_0, ECOENV_UDP_JOKER_0, etc.).
# The CMake target name carries the observable_fun_ prefix to avoid conflicts
# with any top-level target of the same name.
function(add_observable_fun_service NAME)
    set(TARGET "observable_fun_${NAME}")
    add_executable(${TARGET} ${NAME}/main.cpp)
    set_target_properties(${TARGET} PROPERTIES OUTPUT_NAME ${NAME})
    target_link_libraries(${TARGET} PRIVATE ekocpp ekocpp_otlp_traces)
    target_include_directories(${TARGET} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
endfunction()

add_observable_fun_service(fortunes)
add_observable_fun_service(joker)
add_observable_fun_service(lottery)
add_observable_fun_service(magic_eight_ball)
add_observable_fun_service(time_reporter)
add_observable_fun_service(tracker)
add_observable_fun_service(router)
