if (UPDOWNRT_ENABLE_LIBRARIES)
    add_custom_target(libraries)

    set(UPDOWN_RUNTIME_INSTALL_DIR "updown")
    set(UPDOWNSIMRT_LIBRARY_SRC 
        SpMalloc/testSpMalloc.cpp
    )

    set(UPDOWNSIMRT_PYTHON_LIBRARY_SRC2BIN
        #SpMalloc/testSpMallocEFA.py
        SpMalloc/spmalloc_test_exe.py
    )

    set(UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/libraries")

    set(UPDOWNSIMRT_PYTHON_LIBRARY_SRC
        LMStaticMaps/LMStaticMap.udwh
        UDMapShuffleReduce/Macro.py
        UDMapShuffleReduce/GlobalSync.py
        UDMapShuffleReduce/KeyValueSetTPL.py
        UDMapShuffleReduce/KVMapShuffleReduceTPL.py
        UDMapShuffleReduce/KVMSRMachineConfig.py
        UDMapShuffleReduce/ScratchpadCache.py
        UDMapShuffleReduce/linkable/LinkableGlobalSync.py
        UDMapShuffleReduce/KVMSRMachineConfig.py
        dramalloc/dramalloc.py
        dramalloc/dramalloc_linkable.py
    )

    if(UPDOWN_ENABLE_FASTSIM)
        set(DEPS UDLibs UpDownBASimRuntimeStatic UpDownSimRuntimeStatic m)
    elseif(UPDOWN_ENABLE_ASST)
        set(DEPS UpDownBASimRuntimeStatic UpDownSimRuntimeStatic LaneElements ISAElements m rt)
    else ()
        include_directories(${GEM5_BASE_DIR}/include/)
        link_directories(${GEM5_BASE_DIR}/util/m5/build/x86/out)
        set(DEPS UDLibs UpDownBASimRuntimeStatic UpDownSimRuntimeStatic LaneElements ISAElements m rt m5)
        # set(DEPS UpDownBASimRuntimeStatic UpDownSimRuntimeStatic LaneElements ISAElements m rt m5)
    endif ()

    foreach (LIBRARY_SRC ${UPDOWNSIMRT_LIBRARY_SRC})
        get_filename_component(BARENAME ${LIBRARY_SRC} NAME)
        string(REGEX REPLACE "[.]cpp$" "" LIBRARY_NAME ${BARENAME})
        add_executable(${LIBRARY_NAME} ${LIBRARY_SRC})
        target_link_libraries(${LIBRARY_NAME} ${DEPS})

        INSTALL(TARGETS ${LIBRARY_NAME}
            RUNTIME DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH}
        )
    endforeach()

    if(UPDOWN_ENABLE_BASIM)
        set(assem_prog "efa2bin.py")
        foreach(PYFILE IN LISTS UPDOWNSIMRT_PYTHON_LIBRARY_SRC2BIN)
            get_filename_component(PYFILEPATH ${PYFILE} REALPATH) 
            string(REGEX REPLACE "[.]py$" ".bin" PYBIN ${PYFILE})
        get_filename_component(PYBINFILE ${PYBIN} NAME)
            add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE}
                               COMMAND ${PYTHON_EXECUTABLE} ${assem_prog}
                               ARGS --efa ${PYFILEPATH} --outpath ${CMAKE_CURRENT_BINARY_DIR} --toplinker
                               WORKING_DIRECTORY ${UPDOWN_ASSEMBLER}
                               DEPENDS ${PYFILEPATH})
            list(APPEND UPDOWNSIMRT_PYTHON_UBENCH_BIN ${CMAKE_CURRENT_BINARY_DIR}/${PYBINFILE})
        endforeach()
        add_custom_target(UpdownSimRuntimePythonBin ALL DEPENDS ${UPDOWNSIMRT_PYTHON_UBENCH_BIN})
    endif()

    INSTALL(FILES ${UPDOWNSIMRT_PYTHON_LIBRARY_SRC} DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH})
    INSTALL(FILES ${UPDOWNSIMRT_PYTHON_UBENCH_BIN} DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH})

    # set(UPDOWN_DRAMALLOC_LIBRARY_SRC
    #     dramalloc/dramalloc_service_core.cpp
    #     dramalloc/rtree.cpp
    #     dramalloc/alloc.cpp
    # )

    # foreach (LIBRARY_SRC ${UPDOWNSIMRT_LIBRARY_SRC})
    #     get_filename_component(BARENAME ${LIBRARY_SRC} NAME)
    #     string(REGEX REPLACE "[.]cpp$" "" LIBRARY_NAME ${BARENAME})
    #     # add_executable(${LIBRARY_NAME} ${LIBRARY_SRC})
    #     target_link_libraries(${LIBRARY_NAME} ${DEPS})

    #     string(CONCAT LIBRARY_NAME_DYNAMIC "${LIBRARY_NAME}" "")
    #     string(CONCAT LIBRARY_NAME_STATIC "${LIBRARY_NAME}" "Static")
    #     add_library(${LIBRARY_NAME_DYNAMIC} SHARED ${APPS_SRC})
    #     add_library(${LIBRARY_NAME_DYNAMIC} STATIC ${APPS_SRC})

    #     set(UPDOWN_RUNTIME_LIBRARY_INSTALL_LIB "{UPDOWN_RUNTIME_INSTALL_PATH}/lib")

    #     INSTALL(TARGETS ${LIBRARY_NAME}
    #         RUNTIME DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH}
    #     )
    # endforeach()

    set(UPDOWN_RUNTIME_LIB "${UPDOWN_RUNTIME_INSTALL_DIR}/lib")
    set(UPDOWN_RUNTIME_HEADERS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/include")

    # set(UPDOWN_DRAMALLOC_LIBRARY_SRC
    #     dramalloc/dramalloc_service_core.cpp
    #     dramalloc/rtree.cpp
    #     dramalloc/alloc.cpp
    # )

    # foreach (LIBRARY_SRC ${UPDOWNSIMRT_LIBRARY_SRC})
    #     get_filename_component(BARENAME ${LIBRARY_SRC} NAME)
    #     string(REGEX REPLACE "[.]cpp$" "" LIBRARY_NAME ${BARENAME})
    #     # add_executable(${LIBRARY_NAME} ${LIBRARY_SRC})
    #     target_link_libraries(${LIBRARY_NAME} ${DEPS})

    #     string(CONCAT LIBRARY_NAME_DYNAMIC "${LIBRARY_NAME}" "")
    #     string(CONCAT LIBRARY_NAME_STATIC "${LIBRARY_NAME}" "Static")
    #     add_library(${LIBRARY_NAME_DYNAMIC} SHARED ${APPS_SRC})
    #     add_library(${LIBRARY_NAME_DYNAMIC} STATIC ${APPS_SRC})

    #     set(UPDOWN_RUNTIME_LIBRARY_INSTALL_LIB "{UPDOWN_RUNTIME_INSTALL_PATH}/lib")

    #     INSTALL(TARGETS ${LIBRARY_NAME}
    #         RUNTIME DESTINATION ${UPDOWN_RUNTIME_LIBRARY_INSTALL_PATH}
    #     )
    # endforeach()

    set(UPDOWN_RUNTIME_LIB "${UPDOWN_RUNTIME_INSTALL_DIR}/lib")
    set(UPDOWN_RUNTIME_HEADERS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/include")

     if (UPDOWN_ENABLE_FASTSIM)
        add_library(UDLibs dramalloc/dramalloc_service_core.cpp
            dramalloc/dramalloc.hpp dramalloc/rtree.h dramalloc/rtree.cpp
            dramalloc/alloc.h dramalloc/alloc.cpp)
        add_library(UDLibsDynamic SHARED dramalloc/dramalloc_service_core.cpp dramalloc/rtree.cpp dramalloc/alloc.cpp)
        add_library(UDLibsStatic STATIC dramalloc/dramalloc_service_core.cpp dramalloc/rtree.cpp dramalloc/alloc.cpp)
        set_target_properties(UDLibsDynamic PROPERTIES PUBLIC_HEADER 
            "dramalloc/dramalloc.hpp;dramalloc/rtree.h;dramalloc/alloc.h")
        set_target_properties(UDLibsStatic PROPERTIES PUBLIC_HEADER 
            "dramalloc/dramalloc.hpp;dramalloc/rtree.h;dramalloc/alloc.h")
        
            INSTALL(TARGETS UDLibsDynamic
            LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
            ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
            INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
            PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
        )

        INSTALL(TARGETS UDLibsStatic
            LIBRARY DESTINATION ${UPDOWN_RUNTIME_LIB}
            ARCHIVE DESTINATION ${UPDOWN_RUNTIME_LIB}
            INCLUDES DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
            PUBLIC_HEADER DESTINATION ${UPDOWN_RUNTIME_HEADERS_INSTALL_PATH}
        )

        target_link_libraries(UDLibsDynamic PUBLIC UpDownBASimRuntime UpDownSimRuntime UpDownRuntime UDAccelerator LaneElements ISAElements)
        target_link_libraries(UDLibsStatic PUBLIC UpDownBASimRuntimeStatic UpDownSimRuntimeStatic UpDownRuntimeStatic UDAcceleratorStatic)

     else ()
        add_library(UDLibs dramalloc/dramalloc_service_core.cpp
		dramalloc/dramalloc.hpp dramalloc/rtree.h dramalloc/rtree.cpp
		dramalloc/alloc.h dramalloc/alloc.cpp)
     endif()
endif(UPDOWNRT_ENABLE_LIBRARIES)
