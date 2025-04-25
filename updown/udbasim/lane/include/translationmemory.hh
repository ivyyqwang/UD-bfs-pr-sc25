/**
**********************************************************************************************************************************************************************************************************************************
* @file:	translation_memory.hh
* @author:	
* @date:	
* @brief:   Translation Memory for UpDown
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __TRANSLATION_MEMORY__H__
#define __TRANSLATION_MEMORY__H__
#include <cmath>
#include <cstdint>
#include <iostream>
#include "../../../common/include/memorySegments.h"
#include "lanetypes.hh"
#include <vector>

namespace basim
{

class TranslationMemory
{
private:

    // Private UD details
    uint32_t udid;
    int num_uds;
    uint64_t nwid_range;
    bool enable_translation;
    Addr scratchpad_base;

public:
    /* Translation tables for private and global segments */
    std::vector<private_segment_t> private_segments;
    std::vector<global_segment_t> global_segments;

    uint64_t INVALID_ADDR = 0xFFFFFFFFFFFFFFFF;
    // Empty constructor useful for single UD experiments
    TranslationMemory(): udid(0), num_uds(1), scratchpad_base(0), enable_translation(false) {};
    
    // Fastsim TranslationMemory initialization (unit: ud)
    TranslationMemory(uint32_t _udid, int _num_uds, Addr _spbase): udid(_udid), num_uds(_num_uds), nwid_range(_num_uds*64), scratchpad_base(_spbase), enable_translation(false) {};

    // ASST-Fastsim TranslationMemory initialization (unit: updown node)
    TranslationMemory(uint32_t _udid, int _num_uds, Addr _spbase, uint64_t nnodes): udid(_udid), num_uds(_num_uds), nwid_range(nnodes * 2048), scratchpad_base(_spbase), enable_translation(false) {};

    /**
     * @brief Insert a local translation
     * 
     */
    void insertLocalTrans(private_segment_t ps){
        enable_translation = true;
        private_segments.push_back(ps);
    }

    /**
     * @brief Construct and insert a local translation entry
     * 
     */
    void insertLocalTrans(uint64_t virtual_base, uint64_t physical_base, uint64_t size, uint8_t permission);

    /**
     * @brief Insert a global translation
     * 
     */
    
    void insertGlobalTrans(global_segment_t gs){
        enable_translation = true;
        global_segments.emplace_back(gs);
    }

    /**
     * @brief Construct and insert a global translation entry
     * 
     */
    
    void insertGlobalTrans(uint64_t virtual_base, uint64_t physical_base, uint64_t size, uint64_t swizzle_mask, uint8_t permission);

    /**
     * @brief Validate and translate virtual Address to DRAM Address
     * 
     */
    Addr translate_va2pa(Addr addr, int num_words);

    /**
     * @brief Validate and translate local address
     * 
     */
    Addr translate_va2pa_local(Addr addr, int num_words);

    /**
     * @brief Validate and translate global address
     * 
     */
    Addr translate_va2pa_global(Addr addr, int num_words);
    
    /**
     * @brief Validate Scratchpad Address
     * 
     */
    bool validate_sp_addr(Addr addr, int num_bytes);

    /**
     * @brief Validate network id
     * 
     */
    bool validate_nwid(networkid_t nwid);

    /**
     * @brief Reverse translate the physical address to virtual address
     * 
     */
    Addr translate_pa2va(Addr addr, uint8_t flag);

    /**
     * @brief Check if the virtual address is local or global
     * 
     */
    bool isGlobal(Addr addr);

    bool get_enable_translation() { return enable_translation; }

    void dumpSegments();
};


typedef TranslationMemory* TranslationMemoryPtr;
    
}//basim

#endif  //!__TRANSLATION_MEMORY__H__

