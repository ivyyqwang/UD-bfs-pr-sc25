/**
**********************************************************************************************************************************************************************************************************************************
* @file:	isa_cycles.hh
* @author:	
* @date:	
* @brief:   Simple Cycles Defines
**********************************************************************************************************************************************************************************************************************************
**/

#ifndef __ISA_CYCLES__H__
#define __ISA_CYCLES__H__


namespace basim{

#define CTRL_FLOW_CYCLES 1
#define BITWISE_CYCLES 1
#define SPD_WORD_CYCLES 1 // Non-local bank access
#define SB_WORD_CYCLES 1
#define REG_WORD_CYCLES 1
#define SPD_SEND_CYCLES 2
#define REG_SEND_CYCLES 1

// Split up cycles for Floating point by precision
// Intel DP = 5 cycles, 
// others 1/2 of 64bit
#define FP_ARITH_DIVMOD_CYCLES 8
#define FP_ARITH_MUL_CYCLES 1 // Split it up by precision
#define FP_ARITH_ADDSUB_CYCLES 1
#define FP_ARITH_EXPSQRT_CYCLES 8
#define FCNVT_CYCLES 1
#define CMP_WORD_CYCLES 1
#define INT_ARITH_ADDSUB_CYCLES 1
#define INT_ARITH_MULDIV_CYCLES 1
#define TRANSITION_CYCLES 1
#define EV_CYCLES 1
#define MSG_WORD_CYCLES 1
#define THREAD_CTRL_CYCLES 1

// Vector cycles to follow floating point? 
#define VEC_CYCLES 1
#define ATOMIC_CYCLES 1
#define HASH_CYCLES 1
#define PRINT_CYCLES 0
#define ZERO_CYCLES 0
#define ONE_CYCLE 0
#define PRINT_CYCLE 0

}

#endif  //!__ISA_CYCLES__H__