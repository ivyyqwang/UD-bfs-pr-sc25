if (DEFINED CMAKE_GEM5_BASE)
    list(APPEND CMAKE_MODULE_PATH "../../../include")
    include_directories(${GEM5_BASE_DIR}/include/)
    link_directories(${GEM5_BASE_DIR}/util/m5/build/x86/out)
    add_library(UpDownBASimRuntime SHARED ${GEM5_BASE_DIR}/include/gem5/m5ops.h src/basimupdown.cpp)
    add_library(UpDownBASimRuntimeStatic STATIC ${GEM5_BASE_DIR}/include/gem5/m5ops.h src/basimupdown.cpp)
    set_target_properties(UpDownBASimRuntime PROPERTIES PUBLIC_HEADER 
      "include/basimupdown.h;../../../include/gem5/m5ops.h")
    set_target_properties(UpDownBASimRuntimeStatic PROPERTIES PUBLIC_HEADER 
      "include/basimupdown.h;../../../include/gem5/m5ops.h")
else ()
    add_library(UpDownBASimRuntime SHARED src/basimupdown.cpp)
    add_library(UpDownBASimRuntimeStatic STATIC src/basimupdown.cpp)
    set_target_properties(UpDownBASimRuntime PROPERTIES PUBLIC_HEADER 
      "include/basimupdown.h")
    set_target_properties(UpDownBASimRuntimeStatic PROPERTIES PUBLIC_HEADER 
      "include/basimupdown.h")
endif ()

# add_library(UpDownBASimRuntime SHARED src/basimupdown.cpp)
# add_library(UpDownBASimRuntimeStatic STATIC src/basimupdown.cpp)

add_custom_target(basimruntime)

include_directories(BEFORE
    include
    ../udbasim/common/include
    ../udbasim/lane/include
    ../udbasim/isa/include
    ../udbasim/mem/include
    ../udbasim/accel/include
)

if (ENABLE_SQLITE)
    include_directories(BEFORE ../ext/sqlite3)
    target_link_libraries(UpDownBASimRuntime PUBLIC sqlite3 dl)
    target_link_libraries(UpDownBASimRuntimeStatic PUBLIC sqlite3 dl)
endif ()

set(STAT_HEADER "include/basim_stats.hh")

set(UPDOWN_RUNTIME_INSTALL_DIR "updown")

#   if(UPDOWN_ENABLE_ASST_FASTSIM)
#     add_definitions(-DUPDOWN_ENABLE_ASST_FASTSIM)
#   endif()

set(UPDOWN_RUNTIME_HEADERS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/include")
set(UPDOWN_RUNTIME_LIB "${UPDOWN_RUNTIME_INSTALL_DIR}/lib")
set(UPDOWN_RUNTIME_BIN "${UPDOWN_RUNTIME_INSTALL_DIR}/bin")

INSTALL(TARGETS UpDownBASimRuntime
    LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
    ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
    RUNTIME DESTINATION ${UPDOWN_RUNTIME_BIN}
    INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
    PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
)

INSTALL(TARGETS UpDownBASimRuntimeStatic
    LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
    ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
    RUNTIME DESTINATION ${UPDOWN_RUNTIME_BIN}
    INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
    PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
)

INSTALL(FILES ${STAT_HEADER} DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH})
add_definitions(-DUPDOWN_INSTALL_DIR="${CMAKE_INSTALL_PREFIX}/${UPDOWN_RUNTIME_LIB}" -DUPDOWN_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/src" )

if (DEFINED CMAKE_GEM5_BASE)
    target_link_libraries(UpDownBASimRuntime PUBLIC UpDownSimRuntime UpDownRuntime UDAccelerator UDMemory LaneElements ISAElements m rt m5)
    target_link_libraries(UpDownBASimRuntimeStatic PUBLIC UpDownSimRuntimeStatic UpDownRuntimeStatic UDMemoryStatic UDAcceleratorStatic m rt m5)
else()
    target_link_libraries(UpDownBASimRuntime PUBLIC UpDownSimRuntime UpDownRuntime UDAccelerator UDMemory LaneElements ISAElements)
    target_link_libraries(UpDownBASimRuntimeStatic PUBLIC UpDownSimRuntimeStatic UpDownRuntimeStatic UDMemoryStatic UDAcceleratorStatic)
endif ()