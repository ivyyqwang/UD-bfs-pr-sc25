include(GoogleTest)
include(CMakePrintHelpers)

include_directories(BEFORE
  include
  ../common/include
  ../asm/include
  ../lane/include
)

add_library(ISAElements SHARED
            src/atomic_inst.cpp
            src/bitwise_inst.cpp
            src/ctrl_flow_inst.cpp
            src/dat_mov_inst.cpp
            src/dummy_inst.cpp
            src/ev_inst.cpp
            src/fp_arith_inst.cpp
            src/hash_inst.cpp
            src/int_arith_inst.cpp
            src/int_cmp_inst.cpp
            src/msg_inst.cpp
            src/thread_ctrl_inst.cpp
            src/tran_ctrl_inst.cpp
            src/transition.cpp
            src/vec_inst.cpp
            src/debug_inst.cpp
            ../lane/src/translationmemory.cpp # needed to break circular dependence
            ../common/src/logging.cpp
)

add_library(ISAElementsStatic STATIC
            src/atomic_inst.cpp
            src/bitwise_inst.cpp
            src/ctrl_flow_inst.cpp
            src/dat_mov_inst.cpp
            src/dummy_inst.cpp
            src/ev_inst.cpp
            src/fp_arith_inst.cpp
            src/hash_inst.cpp
            src/int_arith_inst.cpp
            src/int_cmp_inst.cpp
            src/msg_inst.cpp
            src/thread_ctrl_inst.cpp
            src/tran_ctrl_inst.cpp
            src/transition.cpp
            src/vec_inst.cpp
            src/debug_inst.cpp
            ../lane/src/translationmemory.cpp
            ../common/src/logging.cpp
)

#target_link_libraries(ISAElementsStatic PUBLIC LaneElementsStatic)
#target_link_libraries(ISAElements PUBLIC LaneElements)

if(${CMAKE_PROJECT_NAME} STREQUAL "UDBASim")
  add_executable(
    isa_tests
    tests/isa_tests.cpp
    tests/inst_decode_test.cpp
  )
  target_compile_features(isa_tests PRIVATE cxx_std_17)

  target_link_libraries(isa_tests PRIVATE gtest ISAElementsStatic LaneElementsStatic)

  gtest_add_tests(isa_tests NULL AUTO)
else()
  set(ISA_INSTALL_DIR "updown")

  set(ISA_LIB "${ISA_INSTALL_DIR}/lib")
  set(ISA_BIN "${ISA_INSTALL_DIR}/bin")

  INSTALL(TARGETS ISAElements
      LIBRARY DESTINATION ${ISA_LIB}
      ARCHIVE DESTINATION ${ISA_LIB}
      RUNTIME DESTINATION ${ISA_BIN}
      INCLUDES DESTINATION ${ISA_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${ISA_HEADERS_INSTALL_PATH}
  )
 
  INSTALL(TARGETS ISAElementsStatic
      LIBRARY DESTINATION ${ISA_LIB}
      ARCHIVE DESTINATION ${ISA_LIB}
      RUNTIME DESTINATION ${ISA_BIN}
      INCLUDES DESTINATION ${ISA_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${ISA_HEADERS_INSTALL_PATH}
  )
endif()
