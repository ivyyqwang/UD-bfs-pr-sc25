### The following variables are used in this Makefile:
UPDOWN_DIR = ../../../../

LINKER_DIR = $(UPDOWN_DIR)linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = $(UPDOWN_DIR)udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = $(UPDOWN_DIR)install
.DEFAULT_GOAL := all

bfs_udweave_exe:   
	python3 $(UDWEAVE) --input vertex_master.udw -o vertex_master.py
	python3 $(UDWEAVE) --input launchers.udw -o launchers.py
	python3 $(UDWEAVE) --input main_master.udw -o main_master.py
	python3 $(LINKER) -L$(UPDOWN_DIR)libraries/UDMapShuffleReduce -L$(UPDOWN_DIR)libraries/dramalloc $(UPDOWN_DIR)libraries/dramalloc/dramalloc_linkable.py vertex_master.py launchers.py main_master.py dram_copy.py -o ../$@ $^


all: bfs_udweave_exe

clean:
	rm -f *.exe 