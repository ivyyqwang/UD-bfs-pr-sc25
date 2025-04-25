include(CMakePrintHelpers)

  if (DEFINED CMAKE_GEM5_BASE)
    list(APPEND CMAKE_MODULE_PATH "../../../include")
    include_directories(${GEM5_BASE_DIR}/include/)
    link_directories(${GEM5_BASE_DIR}/util/m5/build/x86/out)
    add_library(UpDownRuntime SHARED ${GEM5_BASE_DIR}/include/gem5/m5ops.h src/updown.cpp)
    add_library(UpDownRuntimeStatic STATIC ${GEM5_BASE_DIR}/include/gem5/m5ops.h src/updown.cpp)
    target_link_libraries(UpDownRuntime m rt m5)
    target_link_libraries(UpDownRuntimeStatic m rt m5)
  set_target_properties(UpDownRuntime PROPERTIES PUBLIC_HEADER 
      "include/ud_machine.h;include/operands.h;include/networkid.h;include/event.h;include/updown.h;include/updown_config.h;../../../include/gem5/m5ops.h")
  set_target_properties(UpDownRuntimeStatic PROPERTIES PUBLIC_HEADER 
      "include/ud_machine.h;include/operands.h;include/networkid.h;include/event.h;include/updown.h;include/updown_config.h;../../../include/gem5/m5ops.h")
  else ()
    add_library(UpDownRuntime SHARED src/updown.cpp)
    add_library(UpDownRuntimeStatic STATIC src/updown.cpp)
  set_target_properties(UpDownRuntime PROPERTIES PUBLIC_HEADER 
      "include/ud_machine.h;include/operands.h;include/networkid.h;include/event.h;include/updown.h;include/updown_config.h")
  set_target_properties(UpDownRuntimeStatic PROPERTIES PUBLIC_HEADER 
      "include/ud_machine.h;include/operands.h;include/networkid.h;include/event.h;include/updown.h;include/updown_config.h")
  endif ()
    
  include_directories(BEFORE
    include
  )

  set(UPDOWN_RUNTIME_INSTALL_DIR "updown")

  
  set(UPDOWN_RUNTIME_HEADERS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/include")
  set(UPDOWN_RUNTIME_LIB "${UPDOWN_RUNTIME_INSTALL_DIR}/lib")
  set(UPDOWN_RUNTIME_BIN "${UPDOWN_RUNTIME_INSTALL_DIR}/bin")

  INSTALL(TARGETS UpDownRuntime
      LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
      ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
      RUNTIME DESTINATION ${UPDOWN_RUNTIME_BIN}
      INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
  )

  INSTALL(TARGETS UpDownRuntimeStatic
      LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
      ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
      RUNTIME DESTINATION ${UPDOWN_RUNTIME_BIN}
      INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
  )

  add_subdirectory(tests)
  #target_link_libraries(UpDownRuntime PUBLIC)