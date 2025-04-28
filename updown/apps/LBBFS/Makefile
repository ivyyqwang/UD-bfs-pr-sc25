
UPDOWN_ROOT=../../


DRAM_ALLOC_BLOCKSIZE=4096
DRAM_ALLOC_STARTNODE=0



EXEC = LBBFS

UDWEAVE_DIR = $(UPDOWN_ROOT)/udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

LINKER_DIR = $(UPDOWN_ROOT)/linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDASM_DIR=$(UPDOWN_ROOT)/udbasim/assembler
UDASM=efa2bin.py

INSTALL_DIR = $(UPDOWN_ROOT)/install/apps
INSTALLED_DIR = $(UPDOWN_ROOT)/install/updown
UPDOWN_BUILD_ROOT=$(UPDOWN_ROOT)/build


PYTHON=python3
CC=c++
CCFLAGS=-DBASE_PATH=\"$(UPDOWN_ROOT)/install\" \
		-DBASIM=1 \
		-DFASTSIM=1 \
		-DNODE1=1 \
		-DENABLE_SQLITE=1 \
		-DDETAIL_STATS=1 \
		-DMAX_BINS=2000 \
		-DBUCKET_SIZE=20 \
		-DMAX_COUNT_BINS=2000 \
		-DCOUNT_BUCKET_SIZE=1 \
		-DMAX_BYTES_BINS=4096 \
		-DBYTES_BUCKET_SIZE=64 \
		-I./include \
		-I$(HOME)/gem5/include \
		-I$(UPDOWN_ROOT)/include \
		-I$(UPDOWN_ROOT)/linkable \
		-I$(UPDOWN_ROOT)/basimruntime/include \
		-I$(UPDOWN_ROOT)/simruntime/include \
		-I$(UPDOWN_ROOT)/runtime/include \
		-I$(UPDOWN_ROOT)/common/include \
		-I$(UPDOWN_ROOT)/udbasim/isa/include \
		-I$(UPDOWN_ROOT)/udbasim/lane/include \
		-I$(UPDOWN_ROOT)/udbasim/accel/include \
		-I$(UPDOWN_ROOT)/udbasim/common/include \
		-I$(UPDOWN_ROOT)/udbasim/mem/include \
		-I$(UPDOWN_ROOT)/apps/common/glib-adv \
		-I$(UPDOWN_ROOT)/apps/common/glib-core \
		-I$(UPDOWN_ROOT)/apps/common/snap-adv \
		-I$(UPDOWN_ROOT)/apps/common/snap-core \
		-I$(UPDOWN_ROOT)/ext/sqlite3/include \
		-I$(UPDOWN_ROOT)/apps/common/snap-exp \
		-I$(UPDOWN_ROOT)/libraries/dramalloc \
		-I$(UPDOWN_ROOT)/libraries \
		-I$(INSTALLED_DIR)/libraries \
		-c \
		-std=c++17 \
		-fopenmp \
		-g
		# -O3




LDFLAGS=$(UPDOWN_ROOT)/apps/common/snap-core/Snap.o \
		-L$(UPDOWN_ROOT)/libraries/dramalloc \
		-Wl,-rpath,$(UPDOWN_ROOT)/libraries/dramalloc: \
			$(UPDOWN_BUILD_ROOT)/libraries/libUDLibs.a \
			$(UPDOWN_BUILD_ROOT)/basimruntime/libUpDownBASimRuntimeStatic.a \
			$(UPDOWN_BUILD_ROOT)/simruntime/libUpDownSimRuntimeStatic.a \
		/usr/lib/x86_64-linux-gnu/libpython3.10.so \
		$(UPDOWN_BUILD_ROOT)/runtime/libUpDownRuntimeStatic.a \
		$(UPDOWN_BUILD_ROOT)/udbasim/accel/libUDAcceleratorStatic.a \
		$(UPDOWN_BUILD_ROOT)/udbasim/lane/libLaneElementsStatic.a \
		$(wildcard $(UPDOWN_BUILD_ROOT)/udbasim/mem/libUDMemoryStatic.a) \
		$(UPDOWN_BUILD_ROOT)/udbasim/isa/libISAElementsStatic.a \
		$(wildcard $(UPDOWN_BUILD_ROOT)/ext/sqlite3/libsqlite3.a) \
		-ldl \
		-std=c++17 \
		-fopenmp \
		-O3
		

.DEFAULT_GOAL := all
.PHONY:
all: $(EXEC)EFA.bin $(EXEC)

$(EXEC)EFA.bin: $(EXEC)EFA.py
	cd $(UDASM_DIR) && \
	$(PYTHON) $(UDASM) \
		--efa ${CURDIR}/$<  \
		--outpath ${CURDIR}/${dir $@} \
		--toplinker

# Linker
$(EXEC)EFA.py: $(EXEC).py \
					$(UPDOWN_ROOT)/libraries/dramalloc/dramalloc_linkable.py
	python3 $(LINKER) -L./ \
		-L$(UPDOWN_ROOT)/libraries/dramalloc \
		-L$(UPDOWN_ROOT) \
		-L./ \
		-o ./$@ $^

$(EXEC).py: $(EXEC).udw $(INSTALLED_DIR)/libraries/LMStaticMap.udwh
	$(UDWEAVE) -i $< \
			   -I $(INSTALLED_DIR)/libraries/ \
			   -o $@  

$(EXEC).o: $(EXEC).cpp $(EXEC).hpp $(EXEC)EFA.py
	$(CC) $(CCFLAGS)  -o $@ $<

$(EXEC): $(EXEC).o $(EXEC)EFA.bin
	$(CC) $< -o $@ $(LDFLAGS)

convert_el_adj:  convert_el_adj.cpp
	$(CC) -Wall -Wextra -O3 -std=c++20  -o convert_el_adj convert_el_adj.cpp

clean:
	rm -f $(EXEC)
	rm -f $(EXEC).o
	rm -f $(EXEC).py
	rm -f $(EXEC)EFA.hpp
	rm -f $(EXEC)EFA.py
	rm -f $(EXEC)EFA.bin
	rm -Rf __pycache__
	rm -f convert_el_adj
