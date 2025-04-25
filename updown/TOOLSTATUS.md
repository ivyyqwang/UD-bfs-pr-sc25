# UpDown Environments available

Two environments are currently available for developing and testing UD programs listed below

1. UDFastSim - Useful for SW development for UpDown with basic per lane stats.
2. UDGEM5Sim - Useful for performance studies for the UpDown system with more detailed cycle-level stats for Top, UpDown and DRAM

# UpDown Software Available 

All the software being developed (libraries and applications) should run on both environments. Please choose your environment based on your specific experiments/studies. The current list of software available and their support on each environment is listed below. 

| Software | UDFastSim | UDGEM5Sim | Owner|
|----------|-----------|-----------|------|
| **SystemLibraries**|||| 
| UDRuntime|v2| v2 |Jose, Andronicus|
| UD ISA |v2 | v2|Andronicus, Ivy, Marziyeh|
| UDkvmsr |v2|v2|Ivy|
| spMalloc |v1, v2-?|v1, v2-?|Ahsan, Ivy|
| DRAMMalloc | | |Ahsan, Ivy|
| shmem |2/24|2/24|Wenyi|
| sp2dMalloc| | |Ahsan,Ivy|
| **ApplicationLibraries** ||||
| tform |v2 - 2/24|v2 - 2/27|Marziyeh|
| GraphAbstraction | v2 - 2/24 | v2 - 2/24 | Tianshuo |
| UDWeave | | | Jose, Ahsan | 
| **Applications**  ||||
| TC  |v2|v2|Andronicus, Ahsan|
| PR |v2|v1|Ivy|
| JS |v1|v1|Tianshuo|
| BFS |TBD|TBD|Charlie/Amir?|

# UpDown Machine Configurations supported

Below are the machine configurations currently supported in these two environments and as estimate for configurations that will be supported in the future. 

| Machine Configurations        | UDFastSim | UDGEM5Sim | Owner             |
|-------------------------------|-----------|-----------|-------------------|
| 1UD (64 lanes), 1DRAM stack   | [x] 		| [x]		|                   |
| 4UDs, 1DRAM stack             | [x]       | [x]       | Andronicus        |
| 1Node (32UDs, 8DRAM stacks)   | [x]       | 3/4      | Andronicus, Jose,Ivy  | 
| 16Nodes, 128DRAM stacks        | [x]       | 3/7?     | Andronicus, Jose  |