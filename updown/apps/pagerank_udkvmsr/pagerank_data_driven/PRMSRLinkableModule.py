from linker.EFAProgram import efaProgram, EFAProgram

from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
from apps.pagerank_udkvmsr.pagerank_data_driven.PRMSRLinkableConfig import *

@efaProgram
def GenLinkableMapShuffleReduceEFA(efa: EFAProgram):

    testMSR = UDKeyValueMapShuffleReduceTemplate(efa=efa, task_name=TASK_NAME, meta_data_offset=METADATA_OFFSET, debug_flag=DEBUG_FLAG)
    testMSR.set_input_kvset(INPUT_KVSET)
    if ENABLE_REDUCE:
        testMSR.set_intermediate_kvset(INTERMEDIATE_KVSET)
        testMSR.set_output_kvset(OUTPUT_KVSET)
    
    if ENABLE_COMBINE:
        testMSR.setup_cache(cache_offset=CACHE_LM_OFFSET, num_entries=CACHE_NUM_ENTRIES, entry_size=CACHE_ENTRY_SIZE)
    if ENABLE_REDUCE:
        testMSR.set_max_thread_per_lane(max_map_th_per_lane=MAX_MAP_THREAD_PER_LANE, max_reduce_th_per_lane=MAX_REDUCE_THREAD_PER_LANE)
    else:
        testMSR.set_max_thread_per_lane(max_map_th_per_lane=MAX_MAP_THREAD_PER_LANE)

    testMSR.generate_udkvmsr_task()
    
    return efa