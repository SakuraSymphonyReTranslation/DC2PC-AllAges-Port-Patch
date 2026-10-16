cmake_minimum_required(VERSION 3.15)
project(DC2PCPatch)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
set(CMAKE_CXX_STANDARD 20)

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "Error: Building for x64, but x86 expected. Use x86 Native Tools Command Prompt.")
endif()

# Detours library
set(DETOURS_DIR "${CMAKE_SOURCE_DIR}/Detours/src")
include_directories(${DETOURS_DIR})

add_library(detours STATIC
    ${DETOURS_DIR}/detours.cpp
    ${DETOURS_DIR}/modules.cpp
    ${DETOURS_DIR}/disasm.cpp
    ${DETOURS_DIR}/image.cpp
    ${DETOURS_DIR}/creatwth.cpp
    ${DETOURS_DIR}/disolx86.cpp
)

# ============================================================================
# DC2PCPatch.dll - The patch injected by the launcher
# ============================================================================
add_library(DC2PCPatch SHARED
    src/dc2pcpatch.cpp
)

target_link_libraries(DC2PCPatch PRIVATE
    detours
    gdi32
    user32
    advapi32
    comdlg32
)

set_target_properties(DC2PCPatch PROPERTIES
    LINK_FLAGS "/DYNAMICBASE:NO"
    OUTPUT_NAME "DC2PCPatch"
)

# ============================================================================
# DC2PCLauncher.exe - Starts the game and injects DC2PCPatch.dll
# ============================================================================
add_executable(DC2PCLauncher WIN32
    src/launcher.cpp
    src/launcher.rc
)

target_include_directories(DC2PCLauncher PRIVATE src)

target_link_libraries(DC2PCLauncher PRIVATE
    user32
    advapi32
)

set_target_properties(DC2PCLauncher PROPERTIES OUTPUT_NAME "DC2PCLauncher")
