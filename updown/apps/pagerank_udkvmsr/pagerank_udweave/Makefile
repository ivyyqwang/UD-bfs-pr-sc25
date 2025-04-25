### The following variables are used in this Makefile:
LINKER_DIR = ../../../linker/
LINKER = $(LINKER_DIR)EFAlinker.py

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all

linkable_udkmvsr: PRMSRLinkableModule.py
	mkdir -p out
	python3 $(LINKER) -f linkable-module -L./ -L../../../libraries/UDMapShuffleReduce/linkable -L../../../libraries/UDMapShuffleReduce -L../../../  -o ./out/$@ $^

pagerank_msr: pagerankMSR.py PRMSRLinkableModule.py
	mkdir -p out
	python3 $(LINKER) -L./ -L../../../libraries/UDMapShuffleReduce/linkable -L../../../libraries/UDMapShuffleReduce -L../../../  -o ./out/$@ $^

all: linkable_udkmvsr pagerank_msr

clean:
	rm -f *.exe *.out *.o linkable_udkmvsr.py test_array_msr.py