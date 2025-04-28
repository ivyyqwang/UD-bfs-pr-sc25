# UD-bfs-pr-sc25

This repository contains the UpDown accelerator simulator, UpDown application programs and the projection model for the full system design.

## Folder Structure 
The folder structure of the respository

```
├── graph_analytics_and_modeling        # projection model. 
│   ├── julia                           # random graph generators and serial algorithms used for producing work statistics
│   ├── python                          # plotting code for projections.
│   ├── data
│   │   ├── julia_output                # precomputed graph/algorithm statistics used for projections
├── network_modeling                    # discrete event network simulator
│   ├──	data                            # radix 22 PolarStar network adjacency list
│   │  	├── results                     # precomputed network simulation results used for generating Figure 8
│   ├── src                             # source code for the DiscreteEventNetworkSim julia module
│   ├──	test                            # testing code for julia module
│   ├──	plots                           # plotting code for generating Figure 8
├── updown                              # updown simulator
│   ├── apps                            # updown program code and top (CPU) drivers
│   ├── te                              # updown program code and top (CPU) drivers
│   ├── libraries                       # updown software libraries
│   ├── linker                          # updown program linker
│   ├── runtime                         # updown top (CPU) runtime
│   ├── udbasim                         # updown simulator
│   ├── udweave                         # updown UDWeave program compiler
└── common                              # useful utility programs files
```
