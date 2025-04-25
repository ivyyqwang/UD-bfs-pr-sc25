cmake_minimum_required(VERSION 3.13.4)

project(UDBASim VERSION 0.1
                DESCRIPTION "UpDown Bit Accurate Simulator"
                LANGUAGES CXX C)

find_package(OpenMP)

add_compile_options(${OpenMP_CXX_FLAGS})
add_link_options(${OpenMP_CXX_FLAGS})

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake)

set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})

# Enable compile_commands.json generation for clangd and other tools
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)

  # Standalone version of BASIM
  # Optionally set things like CMAKE_CXX_STANDARD, CMAKE_POSITION_INDEPENDENT_CODE here

  # Let's ensure -std=c++xx instead of -std=g++xx
  set(CMAKE_CXX_EXTENSIONS OFF)

  # Google Test requires at least C++14
  set (CMAKE_CXX_STANDARD 17)

  # Let's nicely support folders in IDEs
  set_property(GLOBAL PROPERTY USE_FOLDERS ON)

  # Testing only available if this is the main app
  # Note this needs to be done in the main CMakeLists
  # since it calls enable_testing, which must be in the
  # main CMakeLists.
  include(CTest)

  # Docs only available if this is the main app
  find_package(Doxygen)
  if(Doxygen_FOUND)
    add_subdirectory(docs)
  else()
    message(STATUS "Doxygen not found, not building docs")
  endif()
  include(AddGoogleTest)
  include(CLI)
  include(FetchContent)
  if (BASIM_ENABLE_DEBUG)
    add_compile_definitions(DEBUG_MODE=1)
    set(BASIM_DEBUG True)
    # SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp -ggdb3 -O0 -fsanitize=address -fno-omit-frame-pointer -static-libasan")
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -ggdb -O0")
  else()
    set(BASIM_DEBUG False)
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
  endif()
  enable_testing() # Must be in main file
  add_compile_definitions(BASIM_STANDALONE=1)

  # Compile all the binaries
  find_package(PythonInterp)
  find_package(Python)
  set(assem_prog "efa2binall.py")

  add_subdirectory(common)
  add_subdirectory(isa)
  add_subdirectory(lane)
  add_subdirectory(accel)
  #add_subdirectory(mem)
  add_subdirectory(sim)
  if(BASIM_ENABLE_TESTS)
    add_subdirectory(tests)
    if(BASIM_ASSEMBLE_TESTS)
      message("Will Assemble all tests ${PROJECT_SOURCE_DIR}")
      execute_process(COMMAND ${PYTHON_EXECUTABLE} ${assem_prog}
                      WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/assembler
                      RESULT_VARIABLE exec_result)
      message("result" ${exec_result})
    endif()
  endif()

else()
  # for Fastsim create a library?
  if (${UPDOWN_ENABLE_DEBUG})
    set(BASIM_DEBUG True)
  else()
    set(BASIM_DEBUG False)
  endif()

  message (STATUS "PROJ :$ENV{PROJ}")
  if (DEFINED CMAKE_GEM5_BASE)
    set(GEM5_BASE_DIR "${CMAKE_GEM5_BASE}")
  endif ()

  include_directories(BEFORE
      common/include
      accel/include
      mem/include
      isa/include
      lane/include)

  install(FILES common/include/debug.hh DESTINATION ${UPDOWN_HEADERS_INSTALL_PATH})
  install(FILES common/include/logging.hh DESTINATION ${UPDOWN_HEADERS_INSTALL_PATH})

  ## Building runtime system
  add_subdirectory(common)
  add_subdirectory(isa)
  add_subdirectory(lane)
  add_subdirectory(accel)
  add_subdirectory(mem)
endif()
