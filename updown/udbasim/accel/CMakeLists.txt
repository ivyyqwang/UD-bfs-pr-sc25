include(GoogleTest)
include(CMakePrintHelpers)

include_directories(BEFORE
  include
  ../common/include
  ../isa/include
  ../lane/include
)

add_library(UDAccelerator SHARED src/udaccelerator.cpp)

add_library(UDAcceleratorStatic STATIC src/udaccelerator.cpp)

target_link_libraries(UDAccelerator PUBLIC LaneElements ISAElements)
target_link_libraries(UDAcceleratorStatic PUBLIC LaneElementsStatic ISAElementsStatic)

if(${CMAKE_PROJECT_NAME} STREQUAL "UDBASim")

  add_executable(
    accel_tests
    tests/accel_tests.cpp
    tests/accel_integrated_test.cpp
    tests/buffer_tests.cpp
  )
  target_compile_features(accel_tests PRIVATE cxx_std_17)

  target_link_libraries(accel_tests PRIVATE gtest UDAccelerator)

  gtest_add_tests(accel_tests NULL AUTO)
else()
  
  
  set(UDACCEL_INSTALL_DIR "updown")

  set_target_properties(UDAccelerator PROPERTIES PUBLIC_HEADER 
      "include/udaccelerator.hh")
  set_target_properties(UDAcceleratorStatic PROPERTIES PUBLIC_HEADER 
      "include/udaccelerator.hh")
  set_target_properties(UDAcceleratorStatic PROPERTIES PUBLIC_HEADER 
      "../common/include/logging.hh")

  set(UDACCEL_HEADERS_INSTALL_PATH "${UDACCEL_INSTALL_DIR}/include")
  set(UDACCEL_LIB "${UDACCEL_INSTALL_DIR}/lib")
  set(UDACCEL_BIN "${UDACCEL_INSTALL_DIR}/bin")

  INSTALL(TARGETS UDAccelerator
      LIBRARY DESTINATION ${UDACCEL_LIB}
      ARCHIVE DESTINATION ${UDACCEL_LIB}
      RUNTIME DESTINATION ${UDACCEL_BIN}
      INCLUDES DESTINATION ${UDACCEL_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UDACCEL_HEADERS_INSTALL_PATH}
  )

  INSTALL(TARGETS UDAcceleratorStatic
      LIBRARY DESTINATION ${UDACCEL_LIB}
      ARCHIVE DESTINATION ${UDACCEL_LIB}
      RUNTIME DESTINATION ${UDACCEL_BIN}
      INCLUDES DESTINATION ${UDACCEL_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UDACCEL_HEADERS_INSTALL_PATH}
  )
endif()

