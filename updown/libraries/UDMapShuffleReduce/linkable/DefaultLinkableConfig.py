'''
Default configuration for LMCache and UDMapShuffleReduce
'''

from utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.LMStaticMaps.LMStaticMap import *

# LMCache configuration
CACHE_LM_OFFSET = HEAP_OFFSET
CACHE_NUM_ENTRIES = 32
CACHE_ENTRY_SIZE = 2    # word size
DATA_STORE = OneDimKeyValueSet(name="DATA_STORE", element_size=CACHE_ENTRY_SIZE)
SEND_BUFFER_OFFSET = CACHE_0_OFFSET
DEBUG_FLAG = True
