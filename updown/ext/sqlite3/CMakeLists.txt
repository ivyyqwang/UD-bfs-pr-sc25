add_library(sqlite3 STATIC sqlite3.c sqlite3.h sqlite3ext.h)
set_target_properties(sqlite3 PROPERTIES PUBLIC_HEADER "sqlite3.h")
set_target_properties(sqlite3 PROPERTIES PUBLIC_HEADER "sqlite3ext.h")
set_target_properties(sqlite3 PROPERTIES COMPILE_FLAGS "-fPIC")

add_executable(sqlite sqlite3.c shell.c sqlite3.h sqlite3ext.h)

add_definitions(-DSQLITE_ENABLE_RTREE)
add_definitions(-DSQLITE_ENABLE_FTS5)
add_definitions(-DSQLITE_ENABLE_DBSTAT_VTAB)
add_definitions(-DSQLITE_ENABLE_RBU)
add_definitions(-DSQLITE_ENABLE_STAT4)
add_definitions(-DSQLITE_ENABLE_MATH_FUNCTIONS)

add_definitions(-DSQLITE_DQS=0)
add_definitions(-DSQLITE_DEFAULT_MEMSTATUS=0)
add_definitions(-DSQLITE_DEFAULT_WAL_SYNCHRONOUS=1)

# Disable thread safety
# add_definitions(-DSQLITE_THREADSAFE=0)

include(FindThreads)
target_link_libraries(sqlite m ${CMAKE_THREAD_LIBS_INIT} ${CMAKE_DL_LIBS})
install(TARGETS sqlite RUNTIME DESTINATION "ext/sqlite3/bin")

# install(FILES sqlite3.h sqlite3ext.h DESTINATION "ext/sqlite3/include")
install(TARGETS sqlite3 LIBRARY DESTINATION "ext/sqlite3/lib"
                        ARCHIVE DESTINATION "ext/sqlite3/lib"
                        PUBLIC_HEADER DESTINATION "ext/sqlite3/include")
