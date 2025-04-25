# UpDown Bit Accurate Simulator

This folder consists the Bit Accurate Simulator for the UpDown Accelerator. This is currently in-development and can be run in unittest mode. 
This README will be updated as and when more features are added to the simulator
The organization of the files is also subject to change

## Building simulator and running unittests

In order to build the current version of the elements implemented do the following from the git root folder

1. `cd updown/udbasim`
2. `mkdir build`
3. `cmake -DBASIM_ENABLE_DEBUG=ON -DBASIM_ENABLE_TESTS=ON -DBASIM_ASSEMBLE_TESTS=ON -S . -B build`
4. `cmake --build build -j`

CMAKE Switches
1. `--DBASIM_ENABLE_DEBUG=ON` to the cmake command to switch DEBUG messages ON.
2. `--DBASIM_ENABLE_TESTS=ON` to compile udbasim/tests
3. `--DBASIM_ASSEMBLE_TESTS=ON` generate binaries for all efas in testprogs/efas folder (generated binaries are in testprogs/binaries)

To run unit tests you can run one of the following from `updown/udbasim`

1. `./build/isa/isa_tests`
2. `./build/lane/lane_tests`
3. `./build/accel/accel_tests`
4. `./build/tests/inst_unit_tests`

Assembling  EFA programs 

1. Use the following command to assemble a single program (To be Run under `updown/udbasim/assembler`)

    ``python efa2binall.py --efa ../testprogs/efas/addi.py --outpath ../testprogs/binaries/ --debug-messages --toplinker``

Switches
 `--efa` - Input Program file to generate the binary
 `--outpath` - Path to store output binary file 
 `--debug-messages` - Switch to turn on debug messages from assembler
 `--toplinker` - Switch to include the event labels and their resolved addresses in the binart file


2. Use the following command to assemble all programs in `testprogs/efa` folder. All binaries are generated in `testprogs/binaries` (to be run under `updown/udbasim/assembler`)
    
    ``python efa2binall.py``

