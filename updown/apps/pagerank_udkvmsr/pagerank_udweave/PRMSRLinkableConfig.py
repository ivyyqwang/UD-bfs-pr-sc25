'''
Example configuration file for generating UDKVMSR linkable module.
'''

from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
from libraries.LMStaticMaps.LMStaticMap import *

'''
UDKVMSR program configuration. The following parameters are required:
    task_name:      unique identifier for each UDKVMSR program.
    metadata_offset:   offset of the metadata in bytes. Reserve 32 words on each lane, starting from the offset.
    debug_flag:     enable debug print (optional), default is False
'''
TASK_NAME       = "PageRankMSR"
METADATA_OFFSET = UDKVMSR_0_OFFSET
DEBUG_FLAG      = False
MAX_MAP_THREAD_PER_LANE     = 24
MAX_REDUCE_THREAD_PER_LANE  = 220

# The usage of kv_combine is optional. If not enabled, set ENABLE_COMBINE to False.
ENABLE_COMBINE      = True
'''
Cache configuration. Required if kv_combine is used in reduce.
    cache_offset:   scratchpad bank offset (Bytes) for the cache. 
    num_entries:    number of entries per lane
    entry_size:     size of each entry (in words)
'''
CACHE_LM_OFFSET     = HEAP_OFFSET
CACHE_NUM_ENTRIES   = 2048
CACHE_ENTRY_SIZE    = 2

'''
Define the input, intermediate and output key value set. 
Available key value set types:
    OneDimKeyValueSet:          One dimensional array in DRAM, key is implicitly the index of the array, value is the element in the array.
                                Init parameters: 
                                    name         - name of the key value set
                                    element_size - size of each element in the array (in words)
    IntermediateKeyValueSet:    Dummy set for intermediate key-value pair emitted by map task.
                                Init parameters:
                                    name        - name of the key value set
                                    key_size    - size of the key (in words)
                                    value_size  - size of the value (in words)
    SHTKeyValueSet:             Multi-word scalable hash table. 
                                Init parameters:
                                    name        - name of the key value set
                                    value_size  - size of the value (in words)
    SingleWordSHTKeyValueSet:   Single-word scalable hash table.
                                Init parameters:
                                    name        - name of the key value set
'''
# Input array configuration
INPUT_ARRAY_ELEMENT_SIZE = 4
INPUT_KVSET = OneDimKeyValueSet(name=f"{TASK_NAME}_input", element_size=INPUT_ARRAY_ELEMENT_SIZE, bypass_gen_partition=True)

# Reduce is optional. If not enabled, set ENABLE_REDUCE to False.
ENABLE_REDUCE   = True    
# Intermediate key value pair configuration
INTERMEDIATE_KEY_SIZE   = 1
INTERMEDIATE_VALUE_SIZE = 1
INTERMEDIATE_KVSET = IntermediateKeyValueSet(name=f"{TASK_NAME}_intermediate", key_size=INTERMEDIATE_KEY_SIZE, value_size=INTERMEDIATE_VALUE_SIZE)

# Output array configuration
OUTPUT_ARRAY_ELEMENT_SIZE = 1
OUTPUT_KVSET = OneDimKeyValueSet(name=f"{TASK_NAME}_output", element_size=OUTPUT_ARRAY_ELEMENT_SIZE)
