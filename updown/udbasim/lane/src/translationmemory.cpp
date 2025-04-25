#include "translationmemory.hh"
#include "../../../common/include/memorySegments.h"
#include "types.hh"
#include <cstdio>
#include "debug.hh"
#include <cstdlib>
#include "lanetypes.hh"

namespace basim 
{
    void TranslationMemory::insertLocalTrans(Addr virtual_base, Addr physical_base, uint64_t size, uint8_t permission) {
        BASIM_INFOMSG("Updown %d (nwid between %d and %d) inserts private translation entry {virtual base = %ld(0x%lx), physical base = %ld(0x%lx), size = %ld (%fGB), access permission = %d}", 
                udid, udid << 6, ((udid + 1) << 6) - 1, virtual_base,  virtual_base, 
                physical_base, physical_base, size, size / std::pow(1024, 3), permission);

        enable_translation = true;
        private_segment_t ps = private_segment_t(virtual_base, virtual_base + size, 
            physical_base, permission);
        private_segments.insert(private_segments.begin(),ps);
        //ps.print_info();
    }

    void TranslationMemory::insertGlobalTrans(Addr virtual_base, Addr physical_base, uint64_t size, uint64_t swizzle_mask, uint8_t permission) {
        BASIM_INFOMSG("Updown %d (nwid between %d and %d) inserts global translation entry {virtual base = %ld(0x%lx), physical base = %ld(0x%lx), size = %ld (%fGB), swizzle mask = %ld(0x%lx), access permission = %d}", 
                udid, udid << 6, ((udid + 1) << 6) - 1, virtual_base,  virtual_base, 
                physical_base, physical_base, size, size / std::pow(1024, 3), swizzle_mask, swizzle_mask, permission);
                
        enable_translation = true;
        global_segment_t gs = global_segment_t(virtual_base, virtual_base + size, swizzle_mask,
            physical_base, permission);
        global_segments.emplace_back(gs);
        // gs.print_info();
    }

    Addr TranslationMemory::translate_va2pa(Addr addr, int num_words) {
        BASIM_INFOMSG("Validating DRAM address on updown %d: %lu(0x%lx) length: %d", udid, addr, addr, num_words);
        // Direct mapping if no translation entry is added
        if (!enable_translation) {
            BASIM_INFOMSG("No translation entry is added on updown %d\n", udid);
            return addr;
        }

        for (auto seg : private_segments) {
            if (seg.contains(addr) && seg.contains(addr + (num_words-1) * 8)) {
                //seg.print_info();
                Addr pa = seg.getPhysicalAddr(addr);
                BASIM_INFOMSG("Translate DRAM address %lu(0x%lx) -> %lu(0x%lx)\n", addr, addr, pa, pa);
                return pa;
            } 
        }

        for (auto seg : global_segments) {
            if (seg.contains(addr) && seg.contains(addr + (num_words-1) * 8)) {
                //seg.print_info();
                // Addr pa = seg.getPhysicalAddr(addr).getNodePhysicalAddress();
                Addr pa = seg.getPhysicalAddr(addr).getCompressed();
                BASIM_INFOMSG("Translate DRAM address %lu(0x%lx) -> %lu(0x%lx)\n", addr, addr, pa, pa);
                return pa;
            }
        }
        // BASIM_ERROR("Could not translate address: %lu(0x%lx)\n", addr, addr);
        // BASIM_ERROR("Translation entry is not found in updown %d", udid);
        return INVALID_ADDR;
    }

    Addr TranslationMemory::translate_va2pa_local(Addr addr, int num_words) {
        BASIM_INFOMSG("Validating local address on updown %d: %lu(0x%lx) length: %d", udid, addr, addr, num_words);
        // Direct mapping if no translation entry is added
        if (!enable_translation) {
            BASIM_INFOMSG("No translation entry is added on updown %d", udid);
            return addr;
        }

        for (auto seg : private_segments) {
            if (seg.contains(addr) && seg.contains(addr + (num_words-1) * 8)) {
                //seg.print_info();
                Addr pa = seg.getPhysicalAddr(addr);
                BASIM_INFOMSG("Translate local address %lu(0x%lx) -> %lu(0x%lx)", addr, addr, pa, pa);
                return pa;
            } 
        }
        // BASIM_ERROR("Could not translate address: %lu(0x%lx)\n", addr, addr);
        // BASIM_ERROR("Translation entry is not found in updown %d", udid);
        return INVALID_ADDR;
    }   

    Addr TranslationMemory::translate_va2pa_global(Addr addr, int num_words) {
        BASIM_INFOMSG("Validating global address on updown %d: %lu(0x%lx) length: %d", udid, addr, addr, num_words);
        // Direct mapping if no translation entry is added
        if (!enable_translation) {
            BASIM_INFOMSG("No translation entry is added on updown %d", udid);
            return addr;
        }

        for (auto seg : global_segments) {
            if (seg.contains(addr) && seg.contains(addr + (num_words-1) * 8)) {
                //seg.print_info();
                // Addr pa = seg.getPhysicalAddr(addr).getNodePhysicalAddress();
                Addr pa = seg.getPhysicalAddr(addr).getCompressed();
                BASIM_INFOMSG("Translate global address %lu(0x%lx) -> %lu(0x%lx)", addr, addr, pa, pa);
                return pa;
            }
        }
        // BASIM_ERROR("Could not translate address: %lu(0x%lx)\n", addr, addr);
        // BASIM_ERROR("Translation entry is not found in updown %d", udid);
        return INVALID_ADDR;
    }

    bool TranslationMemory::isGlobal(Addr addr) {
        for (auto seg : private_segments) {
            if (seg.contains(addr)) {
                BASIM_INFOMSG("Address %lu(0x%lx) is in private memory", addr, addr);
                return false;
            }
        }
        BASIM_INFOMSG("Address %lu(0x%lx) is in global memory", addr, addr);
        return true;
    }

    bool TranslationMemory::validate_sp_addr(Addr addr, int num_bytes) {
        BASIM_INFOMSG("Validating scratchpad address on updown %d: addr = %lu(0x%lx), num_bytes = %d", udid, addr, addr, num_bytes);
        // BASIM_PRINT("Validating scratchpad address on updown %d: addr = %lu(0x%lx), num_bytes = %d", udid, addr, addr, num_bytes);
        return (addr >= scratchpad_base) && ((addr + num_bytes) <= scratchpad_base + SCRATCHPAD_SIZE);
    }

    bool TranslationMemory::validate_nwid(networkid_t nwid) {
        BASIM_INFOMSG("Validating message network id %u on updown %d, nwid range=[0:%d]", (nwid.networkid & 0x7FFFFFF), udid, nwid_range - 1);
        uint32_t netid = (nwid.networkid & 0x7FFFFFF);
        return (netid < nwid_range) && (netid >= 0);
    }

    Addr TranslationMemory::translate_pa2va(Addr pa, uint8_t is_global) {
        BASIM_INFOMSG("Reverse translating %s physical address on updown %d: %lu(0x%lx)",
            is_global?"global":"local", udid, pa, pa);
        // Direct mapping if no translation entry is added
        if (!enable_translation) {
            BASIM_INFOMSG("No translation entry is added on updown %d", udid);
            return pa;
        }

        // flag = 0: private segment, flag = 1: global segment
        if (is_global == 0) {
            for (auto seg : private_segments) {
                if (seg.containsPhysicalAddr(pa)) {
                    //seg.print_info();
                    Addr va = seg.getVirtualAddr(pa);
                    BASIM_INFOMSG("Reverse translate physical address %lu(0x%lx) -> %lu(0x%lx)", pa, pa, va, va);
                    return va;
                } 
            }
        } else {
            for (auto seg : global_segments) {
                if (seg.containsPhysicalAddr(pa)) {
                    //seg.print_info();
                    Addr va = seg.getVirtualAddr(pa);
                    BASIM_INFOMSG("Reverse translate physical address %lu(0x%lx) -> %lu(0x%lx)", pa, pa, va, va);
                    return va;
                }
            }
        }
        
        BASIM_ERROR("Could not reverse translate address: %lu(0x%lx)\n"
                    "Translation entry is not found on updown %d", pa, pa, udid);
        return INVALID_ADDR;
    }

    void TranslationMemory::dumpSegments() {

        printf("Private segments:\n");
        for (auto seg : private_segments) {
            seg.print_info();
        }

        printf("Global segment:\n");
        for (auto seg : global_segments) {
            seg.print_info();
        }
    }
}