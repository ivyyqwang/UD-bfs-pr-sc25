include(CMakePrintHelpers)

if (UPDOWNRT_ENABLE_APPS)

	set(UPDOWN_RUNTIME_INSTALL_DIR "updown")
	set(GEM5_DEPS m5 rt)

	set(APPS_WITH_LIBCONFIG "wf2k2")

	include_directories(
		../apps/common/glib-adv
		../apps/common/glib-core
		../apps/common/snap-adv
		../apps/common/snap-core
		../apps/common/snap-exp
		../libraries/dramalloc
	)

	function (compileAndInstall UPDOWNSIMRT_APPS_SRC UPDOWNSIMRT_PYTHON_APPS_SRC UPDOWNSIMRT_PYTHON_APPS_SRC2BIN)
		
		#message(${CMAKE_SOURCE_DIR})
		#message(${CMAKE_BINARY_DIR})
		#message(${CMAKE_CURRENT_SOURCE_DIR})
		#message(${CMAKE_CURRENT_BINARY_DIR})
		#message(${UPDOWNSIMRT_PYTHON_APPS_SRC2BIN})
		#get_target_property(INC_DIRS config++ INCLUDE_DIRECTORIES)
		#message(STATUS "config++ include directories: ${INC_DIRS}")

		# Extract the workflow and the kernel or "isb" and isb
		get_filename_component(WORKFLOW "${CMAKE_CURRENT_BINARY_DIR}/.." ABSOLUTE)
		get_filename_component(WORKFLOW "${WORKFLOW}" NAME)
		get_filename_component(KERNEL "${CMAKE_CURRENT_BINARY_DIR}" NAME)

		message(DEBUG "workflow: ${WORKFLOW}, kernel: ${KERNEL}")
		set(UPDOWN_RUNTIME_APPS_INSTALL_PATH "${UPDOWN_RUNTIME_INSTALL_DIR}/te/${WORKFLOW}/${KERNEL}")

		if(${UPDOWN_ENABLE_BASIM})
			set(assem_prog "efa2bin.py")
			foreach(PYFILE IN LISTS UPDOWNSIMRT_PYTHON_APPS_SRC2BIN)
				get_filename_component(PYFILEPATH ${PYFILE} REALPATH)
				string(REGEX REPLACE "[.]py$" ".bin" PYBIN ${PYFILE})
				get_filename_component(PYBINFILE ${PYBIN} NAME)
				get_filename_component(PYBINPATH ${PYBIN} PATH)
				message(DEBUG "OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${PYBIN}
				         COMMAND ${PYTHON_EXECUTABLE} ${assem_prog}
				         ARGS --efa ${PYFILEPATH} --outpath ${CMAKE_CURRENT_BINARY_DIR}/${PYBINPATH} --toplinker
				         WORKING_DIRECTORY ${UPDOWN_ASSEMBLER}
				         DEPENDS ${PYFILEPATH}
				")

				add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${PYBINPATH}/${PYBINFILE}
					COMMAND ${PYTHON_EXECUTABLE} ${assem_prog}
					ARGS --efa ${PYFILEPATH} --outpath ${CMAKE_CURRENT_BINARY_DIR}/${PYBINPATH} --toplinker
					WORKING_DIRECTORY ${UPDOWN_ASSEMBLER}
					DEPENDS ${PYFILEPATH})
				list(APPEND UPDOWNSIMRT_PYTHON_APPS_BIN ${CMAKE_CURRENT_BINARY_DIR}/${PYBINPATH}/${PYBINFILE})
			endforeach()
			add_custom_target(${KERNEL} ALL DEPENDS ${UPDOWNSIMRT_PYTHON_APPS_BIN})
			add_dependencies(${KERNEL} libraries)
		endif()


		if (DEFINED CMAKE_GEM5_BASE)
			list(APPEND CMAKE_MODULE_PATH "../../../include")
			cmake_print_variables(GEM5_BASE_DIR)
			include_directories(${GEM5_BASE_DIR}/include/)
			link_directories(${GEM5_BASE_DIR}/util/m5/build/x86/out)
			set(DEPS UDLibs UpDownBASimRuntimeStatic UpDownSimRuntimeStatic m rt m5)
		else ()
			set(DEPS UDLibs UpDownBASimRuntimeStatic UpDownSimRuntimeStatic m)
		endif ()
		link_directories(../libraries/dramalloc)
		foreach (APPS_SRC ${UPDOWNSIMRT_APPS_SRC})
			get_filename_component(BARENAME ${APPS_SRC} NAME)
			string(REGEX REPLACE "[.]cpp$" "" APPS_NAME ${BARENAME})

			if (APPS_NAME IN_LIST APPS_WITH_LIBCONFIG AND NOT ENABLE_LIBCONFIG)
				message(STATUS "Skipping ${APPS_NAME} because it requires libconfig++ and ENABLE_LIBCONFIG is OFF")
				continue()
			endif ()

			add_executable(${APPS_NAME} ${APPS_SRC} ${CMAKE_SOURCE_DIR}/apps/common/snap-core/Snap.o)

			if (APPS_NAME IN_LIST APPS_WITH_LIBCONFIG)
				target_link_libraries(${APPS_NAME} ${DEPS} config++)
			else ()
				target_link_libraries(${APPS_NAME} ${DEPS})
			endif ()

            string(CONCAT APPS_NAME_DYNAMIC "${APPS_NAME}" "_dynamic")
            string(CONCAT APPS_NAME_STATIC "${APPS_NAME}" "_static")
            set(UPDOWN_RUNTIME_APPS_INSTALL_LIB "${UPDOWN_RUNTIME_APPS_INSTALL_PATH}")
            add_library(${APPS_NAME_DYNAMIC} SHARED ${APPS_SRC})
            add_library(${APPS_NAME_STATIC} STATIC ${APPS_SRC})

            INSTALL(TARGETS ${APPS_NAME_DYNAMIC}
                LIBRARY DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_LIB}
                ARCHIVE DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_LIB}
            )

            INSTALL(TARGETS ${APPS_NAME_STATIC}
                LIBRARY DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_LIB}
                ARCHIVE DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_LIB}
            )

			INSTALL(TARGETS ${APPS_NAME}
				RUNTIME DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_PATH}
			)
		endforeach()

		INSTALL(FILES ${UPDOWNSIMRT_PYTHON_APPS_SRC} DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_PATH})
		INSTALL(FILES ${UPDOWNSIMRT_PYTHON_APPS_BIN} DESTINATION ${UPDOWN_RUNTIME_APPS_INSTALL_PATH})

	endfunction()

	add_subdirectory(isb)
endif()
