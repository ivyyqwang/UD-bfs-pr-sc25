### The following variables are used in this Makefile:
LINKER_DIR = ../../../linker/
LINKER = $(LINKER_DIR)EFAlinker.py

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all

linkable_udkmvsr: PRMSRLinkableModule.py
	mkdir -p out
	python3 $(LINKER) -f linkable-module -L./ -L../../../libraries/UDMapShuffleReduce/linkable -L../../../libraries/UDMapShuffleReduce -L../../../  -o ./out/$@ $^

pagerank_pull_dd: pagerankPullDD.py PRMSRLinkableModule.py
	mkdir -p out
	python3 $(LINKER) -L./ -L../../../libraries/UDMapShuffleReduce/linkable -L../../../libraries/UDMapShuffleReduce -L../../../  -o ./out/$@ ../../../libraries/dramalloc/dramalloc_linkable.py $^

all: linkable_udkmvsr pagerank_pull_dd

clean:
	rm -f *.exe *.out *.o linkable_udkmvsr.py pagerank_pull_dd.py