
    if (DEFINED CMAKE_GEM5_BASE)
        list(APPEND CMAKE_MODULE_PATH "../../../include")
        include_directories(${GEM5_BASE_DIR}/include/)
        link_directories(${GEM5_BASE_DIR}/util/m5/build/x86/out)
        add_library(UpDownSimRuntime SHARED ${GEM5_BASE_DIR}/include/gem5/m5ops.h src/simupdown.cpp src/upstream_pyintf.cc)
        add_library(UpDownSimRuntimeStatic STATIC ${GEM5_BASE_DIR}/include/gem5/m5ops.h src/simupdown.cpp src/upstream_pyintf.cc)
        set_target_properties(UpDownSimRuntime PROPERTIES PUBLIC_HEADER 
          "include/simupdown.h;../../../include/gem5/m5ops.h")
        set_target_properties(UpDownSimRuntimeStatic PROPERTIES PUBLIC_HEADER 
          "include/simupdown.h;../../../include/gem5/m5ops.h")
    else ()
        add_library(UpDownSimRuntime SHARED src/simupdown.cpp src/upstream_pyintf.cc)
        add_library(UpDownSimRuntimeStatic STATIC src/simupdown.cpp src/upstream_pyintf.cc)
        set_target_properties(UpDownSimRuntime PROPERTIES PUBLIC_HEADER 
          "include/simupdown.h")
        set_target_properties(UpDownSimRuntimeStatic PROPERTIES PUBLIC_HEADER 
          "include/simupdown.h")
    endif ()

  add_library(UpDownPyIntf STATIC src/upstream_pyintf.cc)

  find_package(Python REQUIRED COMPONENTS Interpreter Development)

  include_directories(${Python_INCLUDE_DIRS})

  include_directories(BEFORE
    include
  )

  set(STAT_HEADER "include/sim_stats.hh")

  set(UPDOWN_RUNTIME_INSTALL_DIR "updown")

      set_target_properties(UpDownPyIntf PROPERTIES PUBLIC_HEADER 
      "include/upstream_pyintf.hh")

  set(UPDOWN_RUNTIME_HEADERS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/include")
  set(UPDOWN_RUNTIME_LIB "${UPDOWN_RUNTIME_INSTALL_DIR}/lib")
  set(UPDOWN_RUNTIME_BIN "${UPDOWN_RUNTIME_INSTALL_DIR}/bin")

  INSTALL(TARGETS UpDownSimRuntime
      LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
      ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
      RUNTIME DESTINATION ${UPDOWN_RUNTIME_BIN}
      INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
  )

  INSTALL(TARGETS UpDownSimRuntimeStatic
      LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
      ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
      RUNTIME DESTINATION ${UPDOWN_RUNTIME_BIN}
      INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
  )

  INSTALL(TARGETS UpDownPyIntf
      LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
      ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
      RUNTIME DESTINATION ${UPDOWN_RUNTIME_BIN}
      INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
  )

  INSTALL(FILES ${STAT_HEADER} DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH})
  INSTALL(DIRECTORY src/emulator DESTINATION ${UPDOWN_RUNTIME_LIB})
  add_definitions(-DUPDOWN_INSTALL_DIR="${CMAKE_INSTALL_PREFIX}/${UPDOWN_RUNTIME_LIB}" -DUPDOWN_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/src" )

  add_subdirectory(tests)

if (DEFINED CMAKE_GEM5_BASE)
  target_link_libraries(UpDownSimRuntime PUBLIC UpDownRuntime ${Python_LIBRARIES} m rt m5)
  target_link_libraries(UpDownSimRuntimeStatic PUBLIC UpDownRuntimeStatic ${Python_LIBRARIES} m rt m5)
else()
  target_link_libraries(UpDownSimRuntime PUBLIC UpDownRuntime ${Python_LIBRARIES})
  target_link_libraries(UpDownSimRuntimeStatic PUBLIC UpDownRuntimeStatic ${Python_LIBRARIES})
endif ()
