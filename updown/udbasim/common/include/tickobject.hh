/**
**********************************************************************************************************************************************************************************************************************************
* @file:	tickobject.hh
* @author:	
* @date:	
* @brief:   Tick Objects for BASIM - all objects that will implement Tick() function	
**********************************************************************************************************************************************************************************************************************************
**/

#ifndef __TICKOBJECT__H__
#define __TICKOBJECT__H__
#include <iostream>
#include "lanetypes.hh"

namespace basim
{
/**
 * @brief Tick Object as a basic object that can be simulated at every clock tick
 * 
 * @todo: do we need pre tick and post tick for all objects?
 * 
 */
class TickObject
{
private:
    // last ticked, object can only be simulated if lasttick < curtick, else skip
    Tick lastTick;
    
public:
    TickObject(): lastTick(0){};

    /* Tick function - all derived objects should define what happens in a clock tick*/    
    virtual void tick(uint64_t timestamp = 0) = 0;

    // Update the lastTick by incremental number
    void update(Tick numticks){lastTick += numticks;}

    // Get the last tick 
    Tick getLastTick(){return lastTick;}
};

typedef TickObject* TickObjectPtr;

}//basim


#endif  //!__TICKOBJECT__H__
