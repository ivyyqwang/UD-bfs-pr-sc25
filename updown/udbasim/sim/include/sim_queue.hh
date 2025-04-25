/**
**********************************************************************************************************************************************************************************************************************************
* @file:	SimQueue.hh
* @date:	
* @brief:   Accelerator Definition similar to updown_config.h
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __SimQueue__H__
#define __SimQueue__H__
#include <iostream>
#include "udaccelerator.hh"
#include "types.hh"
#include "lanetypes.hh"
#include "tickobject.hh"

namespace basim
{
   
    class SimQueue
    {
    private:
        // List of Tickable objects
        std::vector<TickObjectPtr> tickObjects; 

        // Period of the tick objects (frequency) Cycles = ticks * periods to align with gem5 when using that
        // standalone sim can use 1 tick - 1 cycle, period = 1
        uint64_t period;

    public:
        // Default constructor
        SimQueue(): period(0){};

        // Constructor with a specific period
        SimQueue(uint64_t _period): period(_period){};

        // enqueue object
        void addToQueue(TickObjectPtr obj){
            tickObjects.emplace_back(obj);
        }
        
        // peek object lasttick only execute if curtick > lasttick
        Tick checkLast(int idx){
            return tickObjects[idx]->getLastTick();
        }
        
        ~SimQueue(){};
    };

}//basim

#endif
