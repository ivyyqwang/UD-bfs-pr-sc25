include(CMakePrintHelpers)

# Add the source files for the TOP
set(UPDOWNSIMRT_APPS_SRC 
    vertex_split/pick_root.cpp
    vertex_split/split_shuffle.cpp
    vertex_split/split_adj.cpp
    bfs/updown_bfs_push_pull.cpp
    bfs/updown_bfs_dramalloc.cpp
)

# Which files should just be copied to the installation folder? E.g. validation scripts
set(UPDOWNSIMRT_PYTHON_APPS_SRC
    RMAT.py
)

# Files that are compiled into a UD executable
set(UPDOWNSIMRT_PYTHON_APPS_SRC2BIN
    bfs/out/bfs_exe.py
    bfs/out/push_pull_exe.py
)

compileAndInstall("${UPDOWNSIMRT_APPS_SRC}" "${UPDOWNSIMRT_PYTHON_APPS_SRC}" "${UPDOWNSIMRT_PYTHON_APPS_SRC2BIN}")
