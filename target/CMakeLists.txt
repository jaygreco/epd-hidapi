cmake_minimum_required(VERSION 3.13)

set(PICO_SDK_FETCH_FROM_GIT on)

include(pico_sdk_import.cmake)
project(epd C CXX ASM)
set(PICO_BOARD_HEADER_DIRS ${CMAKE_SOURCE_DIR})

pico_sdk_init()

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

add_executable(epd_rawhid)

target_sources(epd_rawhid PUBLIC
    ${CMAKE_CURRENT_LIST_DIR}/main.c
    ${CMAKE_CURRENT_LIST_DIR}/tasks.c
    ${CMAKE_CURRENT_LIST_DIR}/epd/epd/platforms/rp2040_thinkink.c
    ${CMAKE_CURRENT_LIST_DIR}/epd/epd/panels/E2B98FS081.c
    ${CMAKE_CURRENT_LIST_DIR}/tinyusb/tud_callbacks.c
    ${CMAKE_CURRENT_LIST_DIR}/tinyusb/usb_descriptors.c
    )

target_include_directories(epd_rawhid PUBLIC
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/epd/epd/
    ${CMAKE_CURRENT_LIST_DIR}/tinyusb
    )

pico_enable_stdio_usb(epd_rawhid 0)
pico_enable_stdio_uart(epd_rawhid 1)

pico_add_extra_outputs(epd_rawhid)

if ("${CMAKE_BUILD_TYPE}" STREQUAL "Debug")
    message("Building with DEBUG")
    add_compile_definitions("DEBUG")
endif()

target_link_libraries(epd_rawhid 
    pico_stdlib
    hardware_spi
    pico_multicore
    tinyusb_device)
