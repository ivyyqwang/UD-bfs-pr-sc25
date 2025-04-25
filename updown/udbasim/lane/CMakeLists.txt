include(GoogleTest)
include(CMakePrintHelpers)

include_directories(BEFORE
  include
  ../../common/include
  ../common/include
  ../isa/include
)

add_library(LaneElements SHARED 
              src/threadstate.cpp 
              src/instructionmemory.cpp
              src/translationmemory.cpp
              src/udlane.cpp
              ../common/src/util.cpp
              ../common/src/logging.cpp
  )

add_library(LaneElementsStatic STATIC
              src/threadstate.cpp 
              src/instructionmemory.cpp
              src/translationmemory.cpp
              src/udlane.cpp
              ../common/src/util.cpp
              ../common/src/logging.cpp
  )

if(${CMAKE_PROJECT_NAME} STREQUAL "UDBASim")
  add_executable(
    lane_tests
    tests/lane_tests.cpp
    tests/eventq_test.cpp
    tests/opbuffer_test.cpp
    tests/instmem_test.cpp
    tests/threadstate_test.cpp
    tests/streambuffer_tests.cpp
    tests/inst_whitebox_unittests.cpp
    tests/lane_integrated_test.cpp
    tests/instructionexecutor_tests.cpp
  )

  target_compile_features(lane_tests PRIVATE cxx_std_17)

  target_link_libraries(lane_tests PRIVATE gtest LaneElementsStatic ISAElementsStatic)

  gtest_add_tests(lane_tests NULL AUTO)
else()
  set(LANE_INSTALL_DIR "updown")

  set(LANE_LIB "${LANE_INSTALL_DIR}/lib")
  set(LANE_BIN "${LANE_INSTALL_DIR}/bin")

  INSTALL(TARGETS LaneElements
      LIBRARY DESTINATION ${LANE_LIB}
      ARCHIVE DESTINATION ${LANE_LIB}
      RUNTIME DESTINATION ${LANE_BIN}
      INCLUDES DESTINATION ${LANE_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${LANE_HEADERS_INSTALL_PATH}
  )

  INSTALL(TARGETS LaneElementsStatic
      LIBRARY DESTINATION ${LANE_LIB}
      ARCHIVE DESTINATION ${LANE_LIB}
      RUNTIME DESTINATION ${LANE_BIN}
      INCLUDES DESTINATION ${LANE_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${LANE_HEADERS_INSTALL_PATH}
  )

endif()

