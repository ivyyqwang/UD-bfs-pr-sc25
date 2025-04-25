### The following variables are used in this Makefile:
LINKER_DIR = ../../../linker
LINKER = $(LINKER_DIR)/EFAlinker.py

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all

LMCache: LinkableLMCache.py
	mkdir -p modules
	python3 $(LINKER) -f linkable-module -L./ -L ../ -L../../../ -o ./modules/$@ $^

Broadcast: LinkableGlobalSync.py
	mkdir -p modules
	python3 $(LINKER) -f linkable-module -L./ -L ../ -L../../../ -o ./modules/$@ $^

all: LMCache Broadcast

clean:
	rm -f *.exe *.out *.o LMCache.py Broadcast.hpp