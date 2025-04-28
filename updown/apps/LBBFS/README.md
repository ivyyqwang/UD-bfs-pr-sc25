# Introduction
This folder runs the Load Balanced BFS
It reads graph files in the adj format from PBBS (https://www.cs.cmu.edu/~pbbs/benchmarks/graphIO.html)
An example graph in this format is given in tinygraph.adj

A conversion tool convert_el_adj is also provided to convert graphs between a whitespace separated edge list and adj format

# Compile
* The main program is located in `LBBFS.cpp` 
* Execute `make LBBFS`

This must be done after the cmake build and install at the top level


# Execute
Simply run the program `./LBBFS <graph file> <num_cores> <source>`

There are 2048 cores per node, so to run on 1 node use 2048 as input.



The end of the output should look something like
```
BFS is correct
### , iteration number, active_set_size, start_outgoing_size, sim_ticks
###, 0, 1, 1, 21100
###, 1, 1, 4, 21100
###, 2, 3, 3, 20400
total ticks = 62600
```
This indicates that the verification passed, shows the number of simulated cycles each iteration took, and the total number of cycles.

Additional log files can be found in the logs directory names with the graph and number of cores simulated.
