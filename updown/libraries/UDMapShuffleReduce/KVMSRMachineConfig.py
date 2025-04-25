from math import log2

WORD_SIZE           = 8
LOG2_WORD_SIZE      = int(log2(WORD_SIZE))

LANE_PER_UD         = 64
UD_PER_NODE         = 32
LOG2_LANE_PER_UD    = int(log2(LANE_PER_UD))
LOG2_UD_PER_NODE    = int(log2(UD_PER_NODE))
MAX_NUM_NODES       = 16384

FLAG                = 1
OB_REG_BASE         = 8
GP_REG_BASE         = 16

NUM_MOV_IMM_BITS    = 12
MAX_MOV_IMM         = 2 ** NUM_MOV_IMM_BITS

NEW_THREAD_ID       = 255
DRAM_MSG_SIZE       = 8
LANE_MSG_SIZE       = 8