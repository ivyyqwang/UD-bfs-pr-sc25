# 
#
# Download CLI
# gives output on failed tests without having to set an environment variable.
#
#

if(CMAKE_VERSION VERSION_LESS 3.11)
    set(UPDATE_DISCONNECTED_IF_AVAILABLE "UPDATE_DISCONNECTED 1")

    include(DownloadProject)
    download_project(PROJ                cli11
		     GIT_REPOSITORY      https://github.com/CLIUtils/CLI11
		     GIT_TAG             v2.3.2
		     UPDATE_DISCONNECTED 1
		     QUIET
    )

    # CMake warning suppression will not be needed in version 1.9
    add_subdirectory(${cli11_SOURCE_DIR} ${cli11_SOURCE_DIR} EXCLUDE_FROM_ALL)
    unset(CMAKE_SUPPRESS_DEVELOPER_WARNINGS)
else()
    include(FetchContent)
    FetchContent_Declare(
      cli11
      GIT_REPOSITORY https://github.com/CLIUtils/CLI11
      GIT_TAG        v2.3.2
    )
    FetchContent_MakeAvailable(cli11)
endif()


