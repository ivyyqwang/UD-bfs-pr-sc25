from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.LMStaticMaps.LMStaticMap import *

'''
UDKVMSR program configuration. The following parameters are required:
    task_name:      unique identifier for each UDKVMSR program.
    metadata_offset:   offset of the metadata in bytes. Reserve 32 words on each lane, starting from the offset.
    debug_flag:     enable debug print (optional), default is False
'''
TASK_NAME       = "PageRankPullDD"
METADATA_OFFSET = UDKVMSR_0_OFFSET
DEBUG_FLAG      = False
MAX_MAP_THREAD_PER_LANE     = 120

# The usage of kv_combine is optional. If not enabled, set ENABLE_COMBINE to False.
ENABLE_COMBINE      = False

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
INPUT_ARRAY_ELEMENT_SIZE = 8
INPUT_KVSET = OneDimKeyValueSet(name=f"{TASK_NAME}_input", element_size=INPUT_ARRAY_ELEMENT_SIZE, bypass_gen_partition=True, argument_size=3)

# Reduce is optional. If not enabled, set ENABLE_REDUCE to False.
ENABLE_REDUCE   = False
