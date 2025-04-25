# UpDown Key Value Map Shuffle Reduce (UDKVMSR)

## Intro
UpDown key value map shuffle reduce, or in short **UDKVMSR**, is a map-reduce like library for generating and managing large fine-grained parallelism in the UpDown system. The library takes input in the format of key-value pairs, maps independent computation to each pair (which will generate one or more intermediate key-value pairs), shuffles the generated pairs based on the key to reducer, reduces intermediate values for the same key, and outputs the resulted key-value pairs. Each key-value pair is a unit of parallelism. The job of UDKVMSR is to distribute the parallelism across the systems as directed by the user and manage the progress and load-balancing for the user.

## Usage 
### Python Static setup
1. Import the module into UpDown python source code file.

    `from LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate`

2. Initialize the UDKVMSR program by instantiating the UDKeyValueMapShuffleReduceTemplate
    
    `kvmsr = UDKeyValueMapShuffleReduceTemplate(efa: linker.EFAProgram = efa, task_name: str = task_name, meta_data_offset: int = UDKVMSR_METADATA_OFFSET, debug_flag: bool: False)`
    
    Where parameters mean:
    
     - `efa`:                           Instance of the linkable EFAProgram.
     - `task_name`:               String identifier, unique for each UDKVMSR program.
     - `metadata_offset`:   Offset of the metadata in the scratchpad memory. Starting from the offset, reserve `32` words for library internal usage.
     - `debug_flag`:             Optional flag to enable debug print in UDKVMSR, default is False.

3. Set the input, intermediate and output key-value set data structures using the following functions:

     - `set_input_kvset(kvset: KeyValueSetInterface)`
     - `set_intermediate_kvset(kvset: KeyValueSetInterface)`
     - `set_output_kvset(kvset: KeyValueSetInterface)`

     Intermediate and output key value set are optional, required if reduce is used.

    Available key value set implementations can be found in directory `libraries/UDMapShuffleReduce/utils`. User can also use customized data structures for key value set by extending the `KeyValueSetInterface` and implement the abstract functions. 
    - `OneDimKeyValueSet`:                 One dimensional array in DRAM, key is implicitly the index of the array, value is the element in the array.
    <br />
    Init parameters:
        - name         - name of the key value set
        - element_size - size of each element in the array (in words)
    - `IntermediateKeyValueSet`:     Dummy set for intermediate key-value pair emitted by map task.
    <br />
    Init parameters:
        - name        - name of the key value set
        - key_size    - size of the key (in words)
        - value_size  - size of the value (in words)
    - `SHTKeyValueSet`:   Multi-word scalable hash table. 
    <br />
    Init parameters:
        - name        - name of the key value set
        - value_size  - size of the value (in words)
    - `SingleWordSHTKeyValueSet`:   Single-word scalable hash table. 
    <br />
    Init parameters:
        - name        - name of the key value set
    
    The following example sets the input key value set to be SHT with 1 word for key and 3 words for values. The SHT descriptor will be stored at offset 64 on each lane's local scratchpad bank. 
    ~~~
    from libraries.UDMapShuffleReduce.utils.SHTKeyValueSet import SHTKeyValueSet
    ...
    set_input_kvset(SHTKeyValueSet("example_kv_set", key_size=1, value_size=3, desc_lm_offset=64))
    ~~~

4. Optionally, set the lane-level parallelism using:

    `set_max_thread_per_lane(max_map_th_per_lane: int, max_reduce_th_per_lane: int)`
    <br />
    Where parameters mean:
    
     - `max_map_th_per_lane`:         Maximum number of map threads that's concurrently activate in a lane.
     - `max_reduce_th_per_lane`:   Maximum number of reduce threads that's concurrently activate in a lane. Optional, required if reduce is used. 
    
    Note that the sum of the two numbers should not exceeds the maximum thread count on a lane (i.e., 255).

5. Implement map and reduce code, using the following event labels as the entry point:
    - `<task_name>::kv_map`
    <br />
    Event label for map function.
    <br />
    Registers:
        - `X8`:                  Input key.
        - `X9 ~ X{9+n}`:  Input values, where `n` equals to the size of input key-value pair's value in words.
    - `<task_name>::kv_reduce`
    <br />
    Event label for reduce function.
    <br />
    Registers:
        - `X8`:                    Intermediate key emitted from map.
        - `X9 ~ X{9+n}`:  Values, where `n` equals to the size of the intermediate key-value pair's value in words.

    Send an event with label `<task_name>::kv_map_emit` and `<task_name>::kv_reduce_emit` to emit intermediate key-value pairs to reduce and output key-value pairs to output kvset respectively (see definition below).
    
    At the end of map and reduce, send an event with label `<task_name>::kv_map_return` and `<task_name>::kv_reduce_return` to the map and reduce thread to return the control to the UDKVMSR library and terminate the map and reduce thread respectively. 
    
6. Generate the UpDown program code using linker and assemble to binary using assembler. 

Please find the example UDKVMSR program linkable module in `apps/msr_examples/linkable_module`.

## Library interface

### Library defined events

1. **`<task_name>::map_shuffle_reduce`**
    <br />
     UDKVMSR program entry point. UDKVMSR program will be launched on lanes starting from the destination nwid of this event up to number of lanes. 
    <br />
    *Operands* :
    - `dest`:  `nwid` = base lane on which UDKVMSR program will be launched. `tid` = new thread `255`.
    - `cont`:  User-defined continuation event triggered when the UDKVMSR program terminates.
    - `X8`:      Pointer to the partition array (64-bit DRAM address).
    - `X9`:      Number of partitions per lane.
    - `X10`:    Number of lanes.
    - `X11`:    Scratchapd address storing the input kvset metadata.
    - `X12`:    Scratchapd address storing the output kvset metadata. (Optional, only required when output kvset is enabled.)
2. **`<task_name>::kv_map_emit`**
    <br />
    Emit intermediate key-value pairs to reduce.
    <br />
    *Operands* :
    - `dest`:               `nwid` = current lane `X0`. `tid` = new thread `255`.
    - `X8`:                   Intermeidate key to be emitted to the reduce.
    - `X9 ~ X{9+n}`: Intermediate values, where `n` equals to the size of the intermediate key-value pair's value in words.
3. **`<task_name>::kv_reduce_emit`**
    <br />
    Emit output key-value pairs to the output key-value set.
    <br />
    *Operands* :
    - `dest`:               `nwid` = current lane `X0`. `tid` = new thread `255`.
    - `X8`:                   Output key.
    - `X9 ~ X{9+n}`: Output values, where `n` equals to the size of the output key-value pair's value in words.
4. **`<task_name>::kv_map_return`**
    <br />
    Event label to end the map function.Used inside user-defined map function to return the control back to UDKVMSR program to terminate the thread.
    <br />
    *Operands* :
    <br />
    - `dest`:  `nwid` = current lane `X0`. `tid` = current thread.
5. **`<task_name>::kv_reduce_return`**
    <br />
    Event label to end the reduce function. Used inside user-defined reduce function to return the control back to UDKVMSR program to terminate the thread.
    <br />
    *Operands* :
    <br />
    - `dest`:  `nwid` = current lane `X0`. `tid` = current thread.

## Helper libraries and functions
### Libraries

Use `Makefile` in `libraries/UDMapShuffleReduce/linkable` to generate the linkable modules in the `modules` subdirectory.

1. **`Broadcast`**
    <br />
    Helper routine to broadcast data (up to 6 words) to a range of lanes and execute customized event on each lane. 
    <br />
    *Python Static setup* :
    
    - `from LinkableGlobalSync import Broadcast`
    - `broadcast = Broadcast(state: EFAProgram.State, identifier: str, debug_flag: bool)`
    <br />
    Parameters:
        - `state` :            Instance of the linkable EFAProgram state.
        - `identifier` :  String identifier for generating event label.
        - `debug_flag` :  Optional flag to enable debug print, default is False.
    - `get_broadcast_ev_label() -> str`
    <br />
    Get the label of the entry event for broadcast. Alternatively, use `<identifier>::broadcast_global`.
    
    *Library defined events*
    
    - `<identifier>::broadcast_global`
    <br />
    Send an event with this label from user program to a new thread to start the broadcast routine. Data will be broadcast to lanes starting from the destination nwid of this event up to number of lanes.
    <br />
    *Operands* :
        - `dest`:  `nwid` = base lane for this broadcast. `tid` = new thread `255`.
        - `cont`:  User-defined continuation event triggered when broadcast returns.
        - `X8`:      Number of lanes.
        - `X9`:      Event label of the user-defined event to be triggeed on each lane. 
        - `X10 ~ X15`: Data to be broadcasted. Will be operands for the user-defined event. 

2. **`LMCache`**
    <br />
    Software cache implemented using scratchpad memory for atomic operations on DRAM data. Currently, only support write-through policy.
    <br />
    *Python Static setup* :

    - `from LinkableLMCache import LMCache`
    - `LMCache(state: EFAProgram.State, identifier: str, cache_offset: int num_entries: int, entry_size: int, data_store: KeyValueSetInterface, send_buffer_offset: int, combine_op: function = None, ival:int = -1, key_size: int = 1, debug_flag: bool = False)`
    <br />
    Parameters:
        - `state` :              Instance of the linkable EFAProgram state.
        - `identifier` :     String identifier for generating event label.
        - `cache_offset`:  Per lane local cache base offset (Bytes offset relative to the local bank, limited to the 64KB bank size).
        - `num_entries`:    Number of entries for each of lane-private cache segment.
        - `entry_size`:      The size of each cache entry in words.
        - `data_store`:      The key value set used to store the data.
        - `metadata_offset`:  Offset of the metadata in the scratchpad (Bytes). Reserve 16 words. 
        - `combine_func`:   User defined combine function. If not specified, the default combine function is used.
        - `ival`:                  Invalid value for invalid cache entry, default is -1 (0xffffffffffffffff).
        - `key_size`:           Size of the key in words, default is 1.
        - `max_active_threads`:  Maximum number of threads for the cache, default equals to num_entries.
        - `debug_flag` :      Optional flag to enable debug print, default is False.
    
    *Library defined events*

    - `<identifier>::cache_init`
    <br />
    Initialize the cache on all the lanes.
    <br />
    *Operands* :
    
        - `dest`:  `nwid` = base lane where cache starts. `tid` = new thread `255`.
        - `cont`:  User-defined continuation event triggered when initialization returns.
        - `X8`:      Number of lanes whose scratchpad has a segment of the cache.
        
    - `<identifier>::cache_get`
    <br />
    Get the current value for a given key. 
    <br />
    *Operands* :
        - `dest`:       `nwid` = any lane with a send buffer, default current lane. `tid` = new thread `255`.
        - `cont`:       User-defined continuation event triggered when get returns.
        - `X8`:           Key.
    
        *Return operands* :
        
        - `X8`:           Flag, -1 if get fails, otherwise equals to key.
        - `X9 ~ Xn`: Values if get succeeds, otherwise returns key.
        
    - `<identifier>::cache_combine`
    <br />
    Update the value for a given key based on the user-defined combine function.
    <br />
    *Operands* :
        - `dest`:       `nwid` = any lane with a send buffer, default current lane. `tid` = new thread `255`.
        - `cont`:       User-defined continuation event triggered when combine returns.
        - `X8`:           Key.
        - `X9 ~ Xn`: Values to be combined.
    
        *Return operands* :
        
        - `X8`:      Flag, -1 if get fails, otherwise equals to key.
        - `X9`:      Key.