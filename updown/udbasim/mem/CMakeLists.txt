include(GoogleTest)
include(CMakePrintHelpers)

include_directories(BEFORE
  include
  ../common/include
  ../isa/include
  ../lane/include
)

add_library(UDMemory SHARED src/udmemory.cpp)

add_library(UDMemoryStatic STATIC src/udmemory.cpp)

target_link_libraries(UDMemory PUBLIC LaneElements ISAElements)
target_link_libraries(UDMemoryStatic PUBLIC LaneElementsStatic ISAElementsStatic)

if(${CMAKE_PROJECT_NAME} STREQUAL "UDBASim")

  add_executable(
    memory_tests
  )
  target_compile_features(memory_tests PRIVATE cxx_std_17)

  target_link_libraries(memory_tests PRIVATE gtest UDMemory)

  gtest_add_tests(memory_tests NULL AUTO)
else()
  
  
  set(UDMEMORY_INSTALL_DIR "updown")

  set_target_properties(UDMemory PROPERTIES PUBLIC_HEADER 
      "include/udmemory.hh")
  set_target_properties(UDMemoryStatic PROPERTIES PUBLIC_HEADER 
      "include/udmemory.hh")
  set_target_properties(UDMemoryStatic PROPERTIES PUBLIC_HEADER 
      "../common/include/logging.hh")

  set(UDMEMORY_HEADERS_INSTALL_PATH "${UDMEMORY_INSTALL_DIR}/include")
  set(UDMEMORY_LIB "${UDMEMORY_INSTALL_DIR}/lib")
  set(UDMEMORY_BIN "${UDMEMORY_INSTALL_DIR}/bin")

  INSTALL(TARGETS UDMemory
      LIBRARY DESTINATION ${UDMEMORY_LIB}
      ARCHIVE DESTINATION ${UDMEMORY_LIB}
      RUNTIME DESTINATION ${UDMEMORY_BIN}
      INCLUDES DESTINATION ${UDMEMORY_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UDMEMORY_HEADERS_INSTALL_PATH}
  )

  INSTALL(TARGETS UDMemoryStatic
      LIBRARY DESTINATION ${UDMEMORY_LIB}
      ARCHIVE DESTINATION ${UDMEMORY_LIB}
      RUNTIME DESTINATION ${UDMEMORY_BIN}
      INCLUDES DESTINATION ${UDMEMORY_HEADERS_INSTALL_PATH}
      PUBLIC_HEADER DESTINATION ${UDMEMORY_HEADERS_INSTALL_PATH}
  )
endif()

