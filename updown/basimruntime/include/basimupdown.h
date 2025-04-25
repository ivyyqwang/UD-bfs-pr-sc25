/*
 * Copyright (c) 2021 University of Chicago and Argonne National Laboratory
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Author - Jose M Monsalve Diaz
 * Author - Andronicus
 *
 */

#ifndef UPDOWNBASIM_H
#define UPDOWNBASIM_H
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <new>
#include <unordered_map>
#include <string>
#include <utility>
#include <vector>
#include <filesystem>
#include <chrono>
#include <semaphore.h>
#include <pthread.h>
#include <atomic>
#include <thread>

#include "debug.h"
#include "basim_stats.hh"
#include "udaccelerator.hh"
#include "udmemory.hh"
#include "updown.h"
#include "simupdown.h"
#include "lanetypes.hh"
#include "types.hh"

#if defined (ENABLE_SQLITE)
#include "sqlite3.h"
#endif

#define NUMTICKS 100

#ifndef UPDOWN_INSTALL_DIR
#define UPDOWN_INSTALL_DIR "."
#endif

#ifndef UPDOWN_SOURCE_DIR
#define UPDOWN_SOURCE_DIR "."
#endif

namespace UpDown {

typedef struct common_addr{
    basim::Addr addr;
    uint8_t isGlobal; // 0:local 1:global -1:other
    uint64_t node_id;
}common_addr;

/*
  This is a hack as it is possible to have multiple instances of the runtime,
  but only one global logger is allowed. We need to know we are logging from
  which runtime instance.
*/
class BASimUDRuntime_t;
extern BASimUDRuntime_t *curRuntimeInstance;

/**
 * @brief Wrapper class that allows simulation of runtime calls using BASIM 
 *
 * This class inherits from UDRuntime_t, and it overwrites the methods
 * such that they can be simulated using a memory region.
 *
 * This class does not use polymorphism. It just oversubscribes the
 * methods, wrapping the original implementation of the runtime
 *
 * @todo This does not emulate multiple UPDs
 *
 */

class BASimUDRuntime_t : public SimUDRuntime_t {
private:
  // Numticks controls no of ticks a lane will execute before moving on
  uint32_t NumTicks;
  uint64_t globalTick;
  uint64_t simTicks; // can be reset

  // BAsim's Accelerators
  std::vector<basim::UDAcceleratorPtr> uds;
  std::vector<basim::UDMemoryPtr> udMems;
  std::vector<std::vector<struct BASimStats>> simStats;
  std::vector<struct BASimNodeStats> simNodeStats;

  // Num outstanding sends 
  //std::vector<uint32_t> outstanding_sends;
  // Map of EventLabels and Symbols
  std::unordered_map<uint32_t, uint32_t> symbolMap;

  std::chrono::high_resolution_clock::time_point startTime;

  event_t send_event_ev;
  uint32_t send_event_valid;
  
#if defined (ENABLE_SQLITE)
  // Database for storing stats
  sqlite3 *stats_db;
#endif
  /**
   * @brief Initialize standard values
   */
  void initialize(uint64_t numUDperNode, uint64_t nnodes, uint64_t topPerNode);

  /**
   * @brief Initialize the BASIM accelerators and load program
   * 
   * @param progfile 
   * @param _pgbase 
   * 
   * @todo Add the program binary creation to this function or should
   * it be a separate function?
   */
  void initMachine(std::string progfile, basim::Addr _pgbase);

  /**
   * @brief Initialize the BASIM logging
   * 
   * @param log_folder_path
   * 
   */
  void initLogs(std::filesystem::path log_folder_path);

  /**
   * @brief Initialize OpenMP
   */
  void initOMP();

  // uint32_t getMemoryMessageTargetUDNodeID(uint64_t addr);
  uint32_t getMemoryMessageTargetStackID(uint64_t addr, bool isGlobal);

  /**
   * @brief Post Simulation interface to the Accelerators
   *
   * @todo when increasing the number of lanes to multiple UpDowns, this
   * function must be re-implemented
   */
  void postSimulateGem5(uint32_t udid, uint32_t laneID);

  void postSimulate(uint32_t udid, uint32_t laneID);

  bool popDelayedMessageUD(uint32_t udid);

  bool popMemory(uint32_t udnodeid, uint32_t stackID);

  bool popDelayedMessageMEM(uint32_t udnodeid, uint32_t stackID);

  void processMessageM1(std::unique_ptr<basim::MMessage> m);
  void processMessageM2(std::unique_ptr<basim::MMessage> m, uint32_t udnodeid);
  void processMessageM3(std::unique_ptr<basim::MMessage> m);
  void processMessageM3M(std::unique_ptr<basim::MMessage> m);
  void processMessageM4(std::unique_ptr<basim::MMessage> m);
  void processMessageM4M(std::unique_ptr<basim::MMessage> m);

  // void processMessage(std::unique_ptr<basim::MMessage> m, uint8_t is_currentnode, uint32_t udid, uint32_t srcLaneID);

  /**
   * @brief Extract event label symbols from the compiled UpDown binary
   * 
   * @param progfile - .bin file
   */
  void extractSymbols(std::string progfile);

  /**
   * @brief Extract event label names from the compiled UpDown binary
   * 
   * @param progfile - .bin file
   */
  std::unordered_map<uint32_t, char*> extractNames(std::string progfile);

  /**
   * @brief Return the global UD Index for the given network ID
   * 
   * @return uint32_t 
   */
  int getUDIdx(basim::networkid_t);
  
  int getUDIdxForAddr(basim::networkid_t, basim::Addr, bool isGlobal);

  /**
   * @brief Send event operands from the sender queues to the receiver lane.
   * @param eops A pointer to the event operands
   * @param sourceUDID ID of the sending UD
   * @param targetLaneID ID of the receiving lane ID
   */
   void sendEventOperands(int sourceUDID, basim::eventoperands_t *eops, uint32_t targetLaneID);

  
  uint64_t getVirtualAddr(int sourceUDID, uint64_t addr, bool isGlobal);

public:

//   uint64_t nnodes;
  uint64_t nnodes_end;
//   uint64_t nodeID;
  uint64_t numUDperNode;
  basim::BufferPtr receive_message_queue;
  basim::BufferPtr send_message_queue[32];
//   uint64_t status;  // 0: normal, 1:upodown start, 2: upodown end, 3: sync, 4: end
  std::atomic<int> status; // 0: normal, 1:upodown start, 2: upodown end, 3: sync, 4: end
  std::atomic<int> barrier_times_atomic;
  pthread_mutex_t mutex, top_lock;
  pthread_cond_t condStart, condTest;
  networkid_t* test_nwid;
  uint32_t* test_offset;
  word_t* test_expected;
  int* test_addr_flag;
  sem_t semStart;
  sem_t *semSync;
  sem_t *semTest;

  pthread_mutex_t map_lock;
  std::map<pthread_t, int> thread_map;
  std::atomic<int> thread_num;

  uint64_t network_output_limit;
  double num_start_exe;



  uint64_t get_status();
  void set_status(uint64_t _status);
  uint64_t get_barrier_times() override;
  void set_barrier_times(uint64_t _barrier_times) override;




  /**
   * @brief Construct a new BASimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. Python will be disabled. Only simulating memory interactions.
   *
   */
  BASimUDRuntime_t();

  /**
   * @brief Construct a new BASimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten in order to simulate the runtime.
   *
   * @param machineConfig Machine configuration
   */
  BASimUDRuntime_t(ud_machine_t machineConfig);

  /**
   * @brief Construct a new BASimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten.
   *
   * @param machineConfig Machine configuration
   */
  BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile,
                 std::string programName, basim::Addr pgbase, uint32_t numTicks=NUMTICKS);

  BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile, basim::Addr pgbase, 
                  uint32_t numTicks=NUMTICKS, std::string log_subfolder_name="");

  BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile, basim::Addr pgbase, uint64_t nnodes, uint64_t nodeID, uint64_t numUDperNode, uint64_t top_per_node=1, uint32_t numTicks=NUMTICKS,
    std::string log_subfolder_name="");

  void barrier(uint64_t barrier_id) override;
  void barrier() override;

  /**
   * @brief Wrapper function for send_event
   *
   * Calls the emulator and calls the UDRuntime_t::send_event() function
   */
  void send_event(event_t ev) override;
  void send_event2(event_t ev);

  /**
   * @brief Wrapper function for start_exec
   *
   * Calls the emulator and calls the UDRuntime_t::start_exec() function
   */
  void start_exec(networkid_t nwid) override;

  /**
   * @brief Wrapper function for t2ud_memcpy
   *
   * Calls the emulator and calls the UDRuntime_t::t2ud_memcpy() function
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  void t2ud_memcpy(void *data, uint64_t size, networkid_t nwid,
                   uint32_t offset) override;

  /**
   * @brief Wrapper function for ud2t_memcpy
   *
   * Calls the emulator and calls the UDRuntime_t::ud2t_memcpy() function
   *
   * This function copies from the emulator directly into the scratchpad memory
   * and then calls the real runtime function. This allows to keep the logic of
   * the real runtime even though we are simulating the hardware
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  void ud2t_memcpy(void *data, uint64_t size, networkid_t nwid,
                   uint32_t offset) override;

  /**
   * @brief Wrapper function for test_addr
   *
   * Calls the emulator and calls the UDRuntime_t::test_addr() function
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  bool test_addr(networkid_t nwid, uint32_t offset,
                 word_t expected = 1) override;

  bool test_addr_without_exec(networkid_t nwid, uint32_t offset,
                 word_t expected = 1);

  /**
   * @brief Wrapper function for test_wait_addr
   *
   * Calls the emulator and calls the UDRuntime_t::test_wait_addr() function
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  void test_wait_addr(networkid_t nwid, uint32_t offset,
                      word_t expected = 1) override;

  /**
   * @brief Function to dump the memory into a file
   * @param filename file to be dumped into
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
  */
  void dumpMemory(const char* filename, void *vaddr, uint64_t size) override;

  /**
   * @brief Method to dump the memory indicated by the translation tables in the UD
   * accelerator into a file. The translation tables are filled by the DRAMAlloc library and
   * when executing an allocation. One file is created per node. 
   * Make sure, that all writes to the memory region are committed (e.g. after invoking
   * basimruntime::barrier()) to ensure consistency.
   * @param filename file to be dumped into. It will be appended by the nodeID and ".dram.dat".
   * @param nodeID The node ID of the current node which invokes this function. Note that all
   *               nodes need to invoke this method.
   * @return Number of total bytes written
   * @see barrier()
   */
  size_t dumpMemoryTranslation(std::string filename, uint64_t nodeID) override;

  /**
   * @brief Function to load memory from a file
   * @param filename file to be dumped into
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
   * @return std::pair<void *, uint64_t> pointer to the memory and size
  */
  std::pair<void *, uint64_t> loadMemory(const char* filename, void *vaddr = nullptr, uint64_t size = 0) override;

  /**
   * @brief Method to load the dump files created by "dumpMemoryTranslation". It will restore
   * the memory content in each of the nodes and also restore the translation tables in all UD
   * accelerators. One file per node is expected.
   * Invoke this method before instanciating DRAMAlloc in the TOP core.
   * @param filename The filename that the dump should be loaded from. The filename is automatically
   *                 appended by the nodeID and ".dram.dat".
   * @param nodeID The node ID of the node that is currently invoking this method.
   * @return Number of total bytes loaded
   * @see dumpMemoryTranslation
   */
  size_t loadMemoryTranslation(std::string filename, uint64_t nodeID, void* dumpVA) override;

  /**
   * @brief Function to dump the memory into a file
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
   * @param filename file to be dumped into
  */
  void dumpLocalMemory(const char* filename, networkid_t start_nwid = networkid_t(), uint64_t num_lanes = 0) override;

  /**
   * @brief Function to load memory from a file
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
   * @param filename file to be dumped into
   * @return std::pair<networkid_t, uint64_t> load networkid and number of lanes
  */
  std::pair<networkid_t, uint64_t> loadLocalMemory(const char* filename, networkid_t start_nwid = networkid_t(), uint64_t num_lanes = 0) override;


  uint64_t getCurTick(){
    return globalTick;
  }

  uint32_t setNumTicks(uint32_t numTicks){
    NumTicks = numTicks;
    return NumTicks;
  }

  uint32_t getNumTicks(){
    return NumTicks;
  }

  uint64_t getSimTicks(){
    return simTicks;
  }
  
  void reset_sim_ticks() {
    simTicks = 0;
  }

  std::chrono::high_resolution_clock::time_point getStartTime(){
    return startTime;
  }

  // return true if receive message to terminate simluation
  uint64_t consumeRemoteMessages();

  ~BASimUDRuntime_t();

  // Reset stats for all UDs
  void reset_stats();
  // Reset stats for a specific UDs
  void reset_stats(uint32_t lane_num);
  // Reset stats for a specific lane
  void reset_stats(uint32_t ud_id, uint8_t lane_num);

  // Update stats (copy from basim into runtime) for a specific lane
  void update_stats(uint32_t lane_num);
  void update_stats(uint32_t ud_id,
                    uint8_t lane_num);
  
  // Get stats for a specific lane
  struct BASimStats& get_stats(uint32_t lane_num);
  struct BASimStats& get_stats(uint32_t ud_id, uint8_t lane_num);

  void print_histograms(uint32_t ud_id, uint8_t lane_num);
  void print_histograms(uint32_t nwid);
  void print_event_stats(uint32_t ud_id, uint8_t lane_num);
  void print_event_stats(uint32_t nwid);

  void print_stats(uint32_t ud_id, uint8_t lane_num);
  void print_stats(uint32_t lane_num);
  void print_curr_cycle(void);
  void print_node_stats(uint32_t nodeID);
  void reset_node_stats();
  void reset_curr_cycle(void);
  void reset_all_stats();

#ifdef INST_HIST
  uint32_t instCounts[static_cast<size_t>(basim::InstMap::COUNT)];
  void print_inst_hist(const char* filename);
#endif

  void db_write_stats(uint32_t start_nwid, uint32_t num_lanes, const char label[]="default");
  void db_write_event_stats(uint32_t start_nwid, uint32_t num_lanes, const char label[]="default");
  void db_write_node_stats(uint32_t start_node, uint32_t num_nodes, const char label[]="default");
private:
  int db_write_label(const char label[]="default");
  void db_exec(std::string sql);

public:

  /**
  * @brief Post Simulation interface to the Accelerators
  *
  * @todo when increasing the number of lanes to multiple UpDowns, this
  * function must be re-implemented
  */
  bool isIdle(uint32_t udid, uint32_t laneID);
  void simulate(uint32_t udid, uint32_t laneID, uint64_t numTicks, uint64_t timestamp);

  int getNodeIdx(basim::networkid_t);

  common_addr mapSA2PA(basim::Addr addr, uint8_t isGlobal);
  common_addr mapPA2SA(basim::Addr addr, uint8_t isGlobal);

  void lock() override;
  void unlock() override;

  void reorder_freetids() override;
};

} // namespace UpDown

#endif
