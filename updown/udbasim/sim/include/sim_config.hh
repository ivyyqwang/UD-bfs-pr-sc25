/**
**********************************************************************************************************************************************************************************************************************************
* @file:	sim_config.hh
* @date:	
* @brief:   Accelerator Definition similar to updown_config.h
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __SIM_CONFIG__H__
#define __SIM_CONFIG__H__
#include <iostream>
#include "udlane.hh"
#include "types.hh"
#include "lanetypes.hh"

namespace basim
{
   
    // DEFAULT VALUES
    #define DEF_NUM_LANES 64          // Number of lanes per CU
    #define DEF_NUM_UDS 4             // Number of CUs
    #define DEF_NUM_STACKS 8          // Number of Stacks per Node
    #define DEF_NUM_NODES 2           // Number of Nodes in System
    #define DEF_SPMEM_BANK_SIZE 65536 // Scratchpad Memory size per lane
    #define DEF_WORD_SIZE 8           // Wordsize
    #define DEF_MAPPED_SIZE 1UL << 32
    #define DEF_GMAPPED_SIZE 1UL << 32

    #define BASE_SPMEM_ADDR 0x400000000
    // Base address for memory mapped control registers
    #define BASE_CTRL_ADDR 0x600000000
    // Base address mapped memory - This is due to simulation
    #define BASE_SYNC_SPACE 0x7FFF0000
    #define BASE_MAPPED_ADDR 0x80000000
    #define BASE_MAPPED_GLOBAL_ADDR 0x200000000

    // CONTROL SIGNALES OFFSET IN WORDS
    #define EVENT_QUEUE_OFFSET 0x0
    #define OPERAND_QUEUE_OFFSET 0x1
    #define START_EXEC_OFFSET 0x2
    #define LOCK_OFFSET 0x3

    static constexpr uint8_t CREATE_THREAD = 0xFF;

    #define BLOCK_SIZE = 64UL << 20

}//basim

#endif
