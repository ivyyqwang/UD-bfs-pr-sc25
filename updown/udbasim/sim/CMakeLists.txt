include(GoogleTest)
include(CMakePrintHelpers)

include_directories(BEFORE
  include
  ../common/include
  ../isa/include
  ../lane/include
  ../accel/include
)

#add_library(BASimElements src/basim.cpp)

add_executable(
  sim_tests
  src/basim.cpp
  tests/basim_gtests.cpp
  tests/send_gtest.cpp
  tests/send_pseudotest.cpp
)

add_executable(
  basim_test
  src/basim.cpp
  tests/sendr_test.cpp
)

target_compile_features(sim_tests PRIVATE cxx_std_17)
target_compile_features(basim_test PRIVATE cxx_std_17)

target_link_libraries(sim_tests PRIVATE gtest UDAcceleratorStatic)
target_link_libraries(basim_test PRIVATE gtest UDAcceleratorStatic)

gtest_add_tests(sim_tests NULL AUTO)

