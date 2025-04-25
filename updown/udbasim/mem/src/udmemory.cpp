#include "udmemory.hh"
#include "types.hh"
#include "lanetypes.hh"
#include <cstdint>

namespace basim
{   
    UDMemory::UDMemory(uint32_t _udnodeid, uint32_t _numStacks, uint64_t latency, uint64_t bandwidth, uint64_t inter_node_latency) : udnodeid(_udnodeid), numStacks(_numStacks) {
        for (auto i = 0; i < _numStacks; i++) {
            UDMemPtr mem = new UDMem(latency, bandwidth, inter_node_latency);
            udMems.push_back(mem);
        }
    }

    /* Idle Check */
    bool UDMemory::isIdle() {
        bool idle = true;
        for (auto i = 0; i < this->numStacks; i++) {
            idle = idle && udMems[i]->isIdle();
        }
        return idle;
    }

    /* Idle Check */
    bool UDMemory::isIdle(uint32_t stackID) {
        return udMems[stackID]->isIdle();
    }

    /* Tick for Memory */
    void UDMemory::tick(uint64_t timestamp) {
        for (auto i = 0; i < this->numStacks; i++) {
            udMems[i]->tick(timestamp);
        }
    }

    // /* simulate API for memory runs through all stacks */
    // void UDMemory::simulate(uint64_t numTicks, uint64_t timestamp) {
    //     uint64_t simTicks = 0;
    //     while (simTicks < numTicks) {
    //         for (auto i = 0; i < this->numStacks; i++) {
    //             udMems[i]->tick(timestamp);
    //         }
    //         simTicks++;
    //     }
    // }

    // /* Simulate API to call per stack */
    // void UDMemory::simulate(uint32_t stackID, uint64_t numTicks, uint64_t timestamp) {
    //     int simTicks = 0;
    //     while (simTicks < numTicks) {
    //         udMems[stackID]->tick(timestamp);
    //         simTicks++;
    //     }
    // }

    void UDMemory::pushMessage(std::unique_ptr<MMessage> m, uint32_t stackID) {
        udMems[stackID]->pushMessage(std::move(m));
    }

    void UDMemory::pushDelayedMessage(std::unique_ptr<MMessage> m, uint32_t stackID) {
        udMems[stackID]->pushDelayedMessage(std::move(m));
    }

    std::unique_ptr<MMessage> UDMemory::popMessage(uint32_t stackID) {
        return udMems[stackID]->popMessage();
    }

    std::unique_ptr<MMessage> UDMemory::popDelayedMessage(uint32_t stackID) {
        return udMems[stackID]->popDelayedMessage();
    }

    StackStats* UDMemory::getStackStats(uint32_t stackID){
        return udMems[stackID]->getStackStats();
    }

    void UDMemory::resetStats(uint32_t stackID){
        udMems[stackID]->resetStats();
    }

    void UDMemory::updateStats(uint32_t stackID){
        udMems[stackID]->updateStats();
    }

    void UDMemory::updateStats(){
        for (auto stackID = 0; stackID < this->numStacks; stackID++) {
            udMems[stackID]->updateStats();
        }
    }

    UDMemory::~UDMemory() {
        for (auto &mem : udMems) {
            delete mem;
        }
    }
}//basim
