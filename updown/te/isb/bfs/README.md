# BFS Validation README

## Generate input

``` bash
python3 ./RMAT.py --scale <scale> --seed <random_seed> 
```

This will generate 1 file `<filename>` containing edges for an RMAT graph of scale `scale` with random seed set to `random_seed`.
The generated graph has two to the power `scale` number of vertices.
The output graph will be written to a file named `scale_<scale>_seed_<random_seed>_edges.txt` under the `graph` folder.

The RMAT graph generated and used for validation and performance experiments are https://drive.google.com/file/d/1lU61zWGhs0oYQw3HMfrmdEOVdSZ2Gauc/view?usp=drive_link. 

``` bash
./preprocess_bfs_edges <graph.txt> <scale>
```

This will take the `.txt` format edge list and convert it to a binary format file. 
Set `graph.txt` to the output file of RMAT graph generator.
The output binary will be written to a file named `graph.txt_edges.bin ` under the `graph` folder.

## Run vertex splitting program

``` bash
./updown_vertex_split <graph.txt_edges.bin> <num_uds> <max_split_degree> (<sht_start_ud> <num_bucket_per_lane> <num_entry_per_bucket>)
```

Set `graph.txt_edges.bin` to the output file of preprocessing program.
`num_uds` specifies the total number of updowns running the vertex splitting program. The minimum is 2.
The maximum degree after the splitting is controlled by `max_split_degree` argument. A good number for a scale 16 RMAT graph is 500.
Optionally, one can change sht configuration. The default values are 

    1. `sht_start_ud` =  `num_uds` / 2
    2. `num_bucket_per_lane` = 64
    3. `num_entry_per_bucket` = 64
This program will output the split graph in a binary file named `split_scale_<scale>_max_split_degree_<max_split_degree>.bin` under the `graph` folder.

## Run BFS

``` bash
./updown_bfs <graph_file> <num_uds> <root_vid> (<updown_bfs_output_file>)
```

`graph_file` is the output of the vertex splitting program named `split_scale_<scale>_max_split_degree_<max_split_degree>.bin`. 
`num_uds` is the number of UpDowns running the BFS computation.
`root_vid` is the root vertex id of the BFS tree to be computed.
`updown_bfs_output_file` is required for validation. The result BFS tree will be dumped to this file.

## Validate output

``` bash
./reference_bfs <graph_file> <root_vid> (<reference_output_file>)
```

The input parameter is similar to the updown bfs program, except no need to set `num_uds`.

``` bash
diff <updown_bfs_output_file> <reference_output_file>
```

Pass if `diff` doesn't complain. 