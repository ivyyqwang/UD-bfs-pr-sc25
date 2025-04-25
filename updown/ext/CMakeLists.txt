if (ENABLE_SQLITE)
    add_subdirectory(sqlite3)
endif ()

if (ENABLE_LIBCONFIG)
    add_subdirectory(libconfig)
endif()
