/**
**********************************************************************************************************************************************************************************************************************************
* @file:	BASim.hh
* @date:	
* @brief:   Standalone Test Infra for BASIM
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __BASim__H__
#define __BASim__H__
#include <iostream>
#include "udaccelerator.hh"
#include "types.hh"
#include "lanetypes.hh"
#include "tickobject.hh"
#include "sim_config.hh"
#include "sim_queue.hh"
#include "machine.hh"

namespace basim
{
    class BASim
    {
    private:
        // Machine Config for BASIM
        machine_t machine;

        // Mapped DRAM Memory
        uint8_t *MappedMemory;

        // sim_queue
        std::vector<UDAcceleratorPtr> uds;

        // Global Tick
        Tick globalTick;

        // Number of UpDowns;
        int numuds;

        // Period of the tick objects (frequency) Cycles = ticks * periods to align with gem5 when using that
        // standalone sim can use 1 tick - 1 cycle, period = 1
        uint64_t period;

        // Mapped memory manager from UpDown Runtime as is to use for DRAM memory 
        class ud_mapped_memory_t {
        private:
          /**
           * @brief A region in memory.
           *
           * This struct represents a region in memory, full or empty
           *
           */
          struct mem_region_t {
            uint64_t size; // Size of the region
            bool free;     // Is the region free or being used
          };

          // Map to keep track of the free and used regions.
          std::map<void *, mem_region_t> regions_local;  // local segments
          std::map<void *, mem_region_t> regions_global; // global segments area

        public:
          /**
           * @brief Construct a new ud_mapped_memory_t object
           *
           * Initializes the regions with a single region
           * that is free and contains all the elements
           *
           * @param machine information from the description of the current machine
           */
          ud_mapped_memory_t(machine_t &machine) {
            BASIM_INFOMSG("Initializing Mapped Memory Manager for %lu at 0x%lX",
                           machine.MapMemSize, machine.MapMemBase);
            // Create the first segment
            void *baseAddr = reinterpret_cast<void *>(machine.MapMemBase);
            regions_local[baseAddr] = {machine.MapMemSize, true};
            baseAddr = reinterpret_cast<void *>(machine.GMapMemBase);
            regions_global[baseAddr] = {machine.GMapMemSize, true};
          }

          /**
           * @brief Get a new region in memory
           *
           * This is equivalent to malloc, it finds a free region that
           * can allocate the current size, and, if there is free space
           * left, it creates a new region with the remaining free space.
           *
           * @param size size to be allocated in bytes.
           * @return void* pointer to the allocated memory
           */
          void *get_region(uint64_t size, bool global) {
            BASIM_INFOMSG("Allocating new region of size %lu bytes", size);
            // Iterate over the regions finding one that fits

            std::map<void *, mem_region_t> *regions_to_use;
            if (global)
              regions_to_use = &regions_global;
            else
              regions_to_use = &regions_local;
            auto used_reg = regions_to_use->end();
            for (auto it = regions_to_use->begin(); it != regions_to_use->end();
                 ++it) {
              // Check if region is free and have enough size
              if (it->second.free && size <= it->second.size) {
                BASIM_INFOMSG("Found a region at 0x%lX",
                               reinterpret_cast<uint64_t>(it->first));
                used_reg = it;
                break;
              }
            }
            // Check if we found space
            if (used_reg == regions_to_use->end()) {
              BASIM_ERROR("Allocator run out of memory. Cannot allocate %lu bytes",
                           size);
              return nullptr;
            }
            // split the new region
            used_reg->second.free = false;
            uint64_t new_size = used_reg->second.size - size;
            used_reg->second.size = size;
            // Create a new empty region
            if (new_size != 0) {
              void *new_reg = static_cast<char *>(used_reg->first) + size;
              (*regions_to_use)[new_reg] = {new_size, true};
              BASIM_INFOMSG(
                  "Creating a new region 0x%lX with the remaining size %lu",
                  reinterpret_cast<uint64_t>(new_reg), new_size);
            }
            BASIM_INFOMSG("Returning region 0x%lX = {%lu, %s}",
                           reinterpret_cast<uint64_t>(used_reg->first),
                           used_reg->second.size,
                           (used_reg->second.free) ? "Free" : "Used");
            // Return the new pointer
            return used_reg->first;
          }

          /**
           * @brief Remove a region
           *
           * This is equivalent to free. It removes a region from the map
           * and extends the region before or after this one if they are free.
           * Otherwise it creates a new free region
           *
           * @param ptr Pointer to be free. It must be a pointer in the regions map
           *
           */
          void remove_region(void *ptr, bool global) {
            BASIM_INFOMSG("Freeing the space at 0x%lX",
                           reinterpret_cast<uint64_t>(ptr));
            // Find location to free
            std::map<void *, mem_region_t> *regions_to_use;
            if (global)
              regions_to_use = &regions_global;
            else
              regions_to_use = &regions_local;
            auto it = regions_to_use->find(ptr);
            if (it == regions_to_use->end() || it->second.free) {
              BASIM_ERROR("Trying to free pointer 0x%lX that is not in the regions"
                           " or the region is free (double free?)",
                           reinterpret_cast<uint64_t>(ptr));
              return;
            }
            // merge left if free
            if (it != regions_to_use->begin() && std::prev(it, 1)->second.free) {
              uint64_t size = it->second.size;
              it--;
              it->second.size += size;
              BASIM_INFOMSG("Merging left 0x%lX to 0x%lX, adding %lu for a total of "
                             "region with %lu",
                             reinterpret_cast<uint64_t>(it->first),
                             reinterpret_cast<uint64_t>(std::next(it, 1)->first),
                             size, it->second.size);
              BASIM_INFOMSG("Removing previous region at 0x%lX",
                             reinterpret_cast<uint64_t>(it->first));
              regions_to_use->erase(std::next(it, 1));
            }
            // merge right if free
            auto nextIt = std::next(it, 1);
            if (nextIt != regions_to_use->end() && nextIt->second.free) {
              uint64_t size = nextIt->second.size;
              it->second.size += size;
              BASIM_INFOMSG(
                  "Merging right 0x%lX to 0x%lX, adding %lu for a total of "
                  "region with %lu",
                  reinterpret_cast<uint64_t>(it->first),
                  reinterpret_cast<uint64_t>(nextIt->first), size, it->second.size);
              BASIM_INFOMSG("Removing previous region at 0x%lX",
                             reinterpret_cast<uint64_t>(it->first));
              regions_to_use->erase(nextIt);
            }

            // Check if there were no merges
            if (it->first == ptr) {
              BASIM_INFOMSG("No merges performed, just freeing 0x%lX = {%lu, %s}",
                             reinterpret_cast<uint64_t>(it->first), (it->second.size),
                             (it->second.free) ? "Free" : "Used");
              it->second.free = true;
            }
          }
        };
        // Instantiate the mapped memory manager
        ud_mapped_memory_t *MappedMemoryManager;

        // Max Sim Cycles before giving up
        uint64_t max_sim_cycles = 1000;

    private:

        /** Internal helper functions 
         * @brief Helper function to get the UD Index from a network ID
         * 
         * @return int 
         */
        int getUDIdx(networkid_t nwid, machine_t machine){
            return( (nwid.getNodeID() * machine.NumStacks * machine.NumUDs) +
                    (nwid.getStackID() * machine.NumUDs) + 
                    (nwid.getUDID()));
        }
    
        Addr getSPAddr(networkid_t nwid, Addr offset){
            return(nwid.getLaneID()*machine.SPBankSize + offset);
        }

    public:
        // Default constructor
        BASim(): uds(0), period(0), numuds(0){};

        // Constructor with a specific period
#ifdef ASST_FASTSIM
        BASim(machine_t _machine, uint64_t _period=1): machine(_machine), period(_period){
            numuds = this->machine.NumStacks * this->machine.NumUDs;
            uds.reserve(numuds);
            for (auto i = 0; i < numuds; i++) {
                UDAcceleratorPtr udptr = new UDAccelerator(machine.NumLanes, i, machine.LocalMemAddrMode);
                uds.emplace_back(udptr);
            }

        }
#else
        BASim(machine_t _machine, uint64_t _period=1): machine(_machine), period(_period){
            numuds = this->machine.NumNodes * this->machine.NumStacks * this->machine.NumUDs;
            uds.reserve(numuds);
            for (auto i = 0; i < numuds; i++) {
                UDAcceleratorPtr udptr = new UDAccelerator(machine.NumLanes, i, machine.LocalMemAddrMode);
                uds.emplace_back(udptr);
            }

        }
#endif

        inline void reset_memory_manager() {
          MappedMemoryManager = new ud_mapped_memory_t(this->machine);
        }
        // Memory Space similar to what is available with UDRuntime for testing purposes
        // ONLY for dram memory (not for top's view of all memory)
        void initMemoryArrays();

        /**
         * @brief Initializes the machine
         * @todo: Change the pgbase to use the memory address space
         */
        void initMachine(std::string progfile, Addr _pgbase=0);

        /**
         * @brief get Current Tick from simulator
         * 
         * @param void
         * @return Tick
         */
        Tick getCurTick(){
          return globalTick;
        }

        // Memory malloc functions from UD Runtime
        void* mm_malloc(uint64_t size) {
          BASIM_INFOMSG("Calling mm_malloc %lu", size);
          return MappedMemoryManager->get_region(size, false);
        }

        void mm_free(void *ptr) {
          BASIM_INFOMSG("Calling mm_free  0x%lX", reinterpret_cast<uint64_t>(ptr));
          return MappedMemoryManager->remove_region(ptr, false);
        }

        void* mm_malloc_global(uint64_t size) {
          BASIM_INFOMSG("Calling mm_malloc_global %lu", size);
          return MappedMemoryManager->get_region(size, true);
        }

        void mm_free_global(void *ptr) {
          BASIM_INFOMSG("Calling mm_free_global  0x%lX",
                         reinterpret_cast<uint64_t>(ptr));
          return MappedMemoryManager->remove_region(ptr, true);
        }

        // push event operands to a nwid (ud/lane)
        void pushEventOperands(networkid_t nwid, eventoperands_t eops);

        // read scratchpad 
        void t2ud_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset); 
        // write scratchpad 
        void ud2t_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset);

        void postTick(networkid_t nwid);

        // Simulate to be called from Test Top 
        void simulate(int numTicks = 1);


        // Test API
        /* testing api returns value from register of whatever thread is currently active */
        bool testReg(networkid_t nwid, RegId raddr, word_t val);
    
        /* testing api returns value from scratchpad memory */
        bool testSPMem(networkid_t nwid, Addr addr, word_t val);
        
        /* testing api that tests val against value in Mapped memory */
        bool testDRMem(Addr addr, word_t val);
    
    
    };

}//basim

#endif
