# UpDown Assembler

## Files in the folder

```
├── efas                                        # symbolic link to the efa parser and emulator
├── efa2bin.py                                  # script to generating binary from UpDown EFA
├── efa2binall.py                               # script to generating binary for all tests in the basim env
├── efa2bin_interface.py                        # 
├── isa_encodings.py                            # Common Dictionaries Used by Encoder and Decoder 
├── enc_gen.py                                  # Script to Generate the instruction decoder files
├── UpDown_Assembler.py                         # UpDown Assembly Generation Package
├── UpDown_Assembler_helper.py                  # 

```

## Example for generating the binary file:

Command to generate the binary file

`python efa2bin.py --efa ../testprogs/efas/addi.py --outpath ../testprogs/binaries/`

Optional switches

1. `--debug-messages` - turns on assembler Debug Messages
2. `--toplinker` - turns on symbol table dump in the binary
3. `--text-symbol-table` - writes out the symbol table to a text file

## Output Binary File Format

Current Binary format with symbol table is as follows,

```
    Number of events [4B]
    EventLabel0 [4B]
    EventLabel0 Address [4B]
    EventLabel1 [4B]
    EventLabel1 Address [4B]
    .
    .
    .
    Address [8B]
    NumberOfInstructions [8B]
    Transition [4B]
    Instruction0 [4B]
    Instruction1 [4B]

```
## Example Binary File Layout

Example of the binary file layout for an efa with 3 event transitions with 4, 2 and 0 associated actions, respectively:

```
    3 (number of event labels)
    event_label1 
    resolved_event_label1
    event_label2
    resolved_event_label2
    event_label3
    resolved_event_label3
    0 (AddressofEV-TX1 in bytes)
    5 (the number of instruction following the address)
    EV-TX1
    EV-TX1 (action1)
    EV-TX1 (action2)
    EV-TX1 (action3)
    EV-TX1 (action4)
    20 (AddressofEV-TX2 in bytes)
    3
    EV-TX2
    EV-TX2 (action1)
    EV-TX2 (action1)
    32 (AddressofEV-TX3 in bytes)
    1
    EV-TX3

```
## Event Label to Name map

Example of binary file layout for an event name map with 3 entries:
    3 (number of event names/labels)
    event_label1
    event_name_offset1 (in bytes)
    event_name_string1
    event_label2
    event_name_offset2 (in bytes)
    event_name_string2
    event_label3
    event_name_offset3 (in bytes)
    event_name_string3

```  
## Format of offsets at start of file
```
    1. Offset to end of offsets/event list
    2. Offset to start of instructions
    3. Offset to start of strings
    4. Offset to start of event label : name list
    5. Offset to end of file
```
