#include "simupdown.h"
#include "debug.h"
#include "sim_stats.hh"
#include "updown_config.h"
#include "upstream_pyintf.hh"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <sys/mman.h>
#include <utility>
#include <vector>

namespace UpDown {
  /**
   * @brief Construct a new SimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. Python will be disabled. Only simulating memory interactions.
   *
   */
  SimUDRuntime_t::SimUDRuntime_t() : UDRuntime_t(), python_enabled(false) {
    UPDOWN_INFOMSG("Initializing Simulated Runtime with default params");
    UPDOWN_WARNING("No python program. Python will be disabled, only "
                   "simulating memory interactions");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    #ifdef ASST_FASTSIM
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #else
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #endif
    initMemoryArrays();
    // Recalculate address map
    calc_addrmap();
  }

  /**
   * @brief Construct a new SimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten in order to simulate the runtime.
   *
   * @param machineConfig Machine configuration
   */
  SimUDRuntime_t::SimUDRuntime_t(ud_machine_t machineConfig)
      : UDRuntime_t(machineConfig), python_enabled(false) {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_WARNING("No python program. Python will be disabled, only "
                   "simulating memory interactions");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    #ifdef ASST_FASTSIM
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #else
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #endif
    initMemoryArrays();
    // Recalculate address map
    calc_addrmap();
    init_stats();
  }

  /**
   * @brief Construct a new SimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten.
   *
   * @param machineConfig Machine configuration
   */
  SimUDRuntime_t::SimUDRuntime_t(std::string programFile, std::string programName,
                 std::string simulationDir,
                 EmulatorLogLevel printLvl)
      : UDRuntime_t(), programFile(programFile), programName(programName),
        simulationDir(simulationDir), python_enabled() {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    #ifdef ASST_FASTSIM
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #else
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #endif
    initMemoryArrays();
    UPDOWN_INFOMSG("Running file %s Program %s Dir %s", programFile.c_str(),
                   programName.c_str(), simulationDir.c_str());
    initPythonInterface(printLvl);
    // Recalculate address map
    calc_addrmap();
    init_stats();
  }

  /**
   * @brief Construct a new SimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten.
   *
   * @param machineConfig Machine configuration
   */
  SimUDRuntime_t::SimUDRuntime_t(ud_machine_t machineConfig, std::string programFile,
                 std::string programName, std::string simulationDir,
                 EmulatorLogLevel printLvl)
      : UDRuntime_t(machineConfig), programFile(programFile),
        programName(programName), simulationDir(simulationDir),
        python_enabled(true) {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    #ifdef ASST_FASTSIM
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #else
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #endif
    initMemoryArrays();
    UPDOWN_INFOMSG("Running file %s Program %s Dir %s", programFile.c_str(),
                   programName.c_str(), simulationDir.c_str());
    initPythonInterface(printLvl);
    // Recalculate address map
    calc_addrmap();
    init_stats();
  }

  /**
   * @brief Construct a new SimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten. But No Python Interface is enabled
   *
   * @param machineConfig Machine configuration
   */
  SimUDRuntime_t::SimUDRuntime_t(ud_machine_t machineConfig, std::string programFile,
                 std::string programName)
      : UDRuntime_t(machineConfig), programFile(programFile),
        programName(programName),
        python_enabled(false) {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    #ifdef ASST_FASTSIM
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #else
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #endif
    initMemoryArrays();
    UPDOWN_INFOMSG("Running file Program %s Dir %s", programFile.c_str(),
                   programName.c_str());
    // Recalculate address map
    calc_addrmap();
    init_stats();
  }

  /**
   * @brief Construct a new SimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten. But No Python Interface is enabled
   *
   * @param machineConfig Machine configuration
   */
  SimUDRuntime_t::SimUDRuntime_t(ud_machine_t machineConfig, std::string programFile)
      : UDRuntime_t(machineConfig), programFile(programFile),
        python_enabled(false) {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    #ifdef ASST_FASTSIM
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #else
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct SimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    #endif
    initMemoryArrays();
    UPDOWN_INFOMSG("Running Program %s ", programFile.c_str());
    // Recalculate address map
    calc_addrmap();
    init_stats();
  }

void SimUDRuntime_t::initMemoryArrays() {
  // Initializing arrays containning mapped memory
  UPDOWN_INFOMSG("Allocating %lu bytes for mapped memory",
                 this->MachineConfig.MapMemSize);

  // Old way of allocating simulation memory
  // MappedMemory = new uint8_t[this->MachineConfig.MapMemSize];

  // Use mmap to allocate memory to make sure the allocated address is consistent
  MappedMemory = (uint8_t *) mmap(reinterpret_cast<void *>(BASE_MAPPED_ADDR), this->MachineConfig.MapMemSize, PROT_READ | PROT_WRITE, MAP_FIXED_NOREPLACE | MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
  UPDOWN_ERROR_IF(MappedMemory == MAP_FAILED, "Failed to allocate mapped memory at 0x%llX with size %lu", BASE_MAPPED_ADDR, this->MachineConfig.MapMemSize);

  #ifdef ASST_FASTSIM
    UPDOWN_INFOMSG("Allocating %lu bytes for mapped global memory",
                   this->MachineConfig.GMapMemSize/MachineConfig.NumNodes);
    GMappedMemory = new uint8_t[this->MachineConfig.GMapMemSize/MachineConfig.NumNodes];
    this->MachineConfig.PhysGMapMemBase = reinterpret_cast<uint64_t>(GMappedMemory);
    UPDOWN_ERROR_IF(GMappedMemory == NULL, "Failed to allocate mapped global memory with size %lu", this->MachineConfig.GMapMemSize/MachineConfig.NumNodes);
  //   printf("allocate mapped global memory at 0x%llX with size %lu\n", this->MachineConfig.PhysGMapMemBase, this->MachineConfig.GMapMemSize/nnodes);
    // Use mmap to allocate memory to make sure the allocated address is consistent
  //   GMappedMemory = (uint8_t *) mmap(reinterpret_cast<void *>(BASE_MAPPED_GLOBAL_ADDR), this->MachineConfig.GMapMemSize/nnodes, PROT_READ | PROT_WRITE, MAP_FIXED_NOREPLACE | MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
  //   UPDOWN_ERROR_IF(GMappedMemory == MAP_FAILED, "Failed to allocate mapped global memory at 0x%llX with size %lu", this->MachineConfig.PhysGMapMemBase, this->MachineConfig.GMapMemSize/MachineConfig.NumNodes);
  #else
    UPDOWN_INFOMSG("Allocating %lu bytes for mapped global memory",
                   this->MachineConfig.GMapMemSize);
    GMappedMemory = new uint8_t[this->MachineConfig.GMapMemSize];
    this->MachineConfig.PhysGMapMemBase = reinterpret_cast<uint64_t>(GMappedMemory);
    UPDOWN_ERROR_IF(GMappedMemory == NULL, "Failed to allocate mapped global memory with size %lu", this->MachineConfig.GMapMemSize);
  //   printf("allocate mapped global memory at 0x%llX with size %lu\n", this->MachineConfig.PhysGMapMemBase, this->MachineConfig.GMapMemSize);
    // Use mmap to allocate memory to make sure the allocated address is consistent
  //   GMappedMemory = (uint8_t *) mmap(reinterpret_cast<void *>(BASE_MAPPED_GLOBAL_ADDR), this->MachineConfig.GMapMemSize, PROT_READ | PROT_WRITE, MAP_FIXED_NOREPLACE | MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
  //   UPDOWN_ERROR_IF(GMappedMemory == MAP_FAILED, "Failed to allocate mapped global memory at 0x%llX with size %lu", this->MachineConfig.PhysGMapMemBase, this->MachineConfig.GMapMemSize);
  #endif



  UPDOWN_INFOMSG("Allocating %lu bytes for Scratchpad memory", this->MachineConfig.SPSize());
  // Old way of allocating simulation LM memory
  ScratchpadMemory = new uint8_t[this->MachineConfig.SPSize()];
  UPDOWN_ERROR_IF(ScratchpadMemory == NULL, "Failed to allocate mapped memory with size %lu for LM", this->MachineConfig.SPSize());
  // Use mmap to allocate memory to make sure the allocated address is consistent
//   ScratchpadMemory = (uint8_t *) mmap(reinterpret_cast<void *>(BASE_SPMEM_ADDR), this->MachineConfig.SPSize(), PROT_READ | PROT_WRITE, MAP_FIXED_NOREPLACE | MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
//   UPDOWN_ERROR_IF(ScratchpadMemory == MAP_FAILED, "Failed to allocate mapped memory at 0x%llX with size %lu for LM", BASE_SPMEM_ADDR, this->MachineConfig.SPSize());

  uint64_t size_control =
      this->MachineConfig.CapNumNodes * this->MachineConfig.CapNumStacks *
      this->MachineConfig.CapNumUDs * this->MachineConfig.CapNumLanes *
      this->MachineConfig.CapControlPerLane;
  UPDOWN_INFOMSG("Allocating %lu bytes for control", size_control);
  ControlMemory = new uint8_t[size_control];
  UPDOWN_ERROR_IF(ControlMemory == NULL, "Failed to allocate mapped memory with size %lu for Control Memory", size_control);

  // Changing the base locations for the simulated memory regions
  this->MachineConfig.MapMemBase = reinterpret_cast<uint64_t>(MappedMemory);
  UPDOWN_INFOMSG("MapMemBase changed to 0x%lX", this->MachineConfig.MapMemBase);
//   this->MachineConfig.GMapMemBase = reinterpret_cast<uint64_t>(GMappedMemory);
//   UPDOWN_INFOMSG("GMapMemBase changed to 0x%lX", this->MachineConfig.GMapMemBase);
  this->MachineConfig.UDbase = reinterpret_cast<uint64_t>(ScratchpadMemory);
  this->MachineConfig.SPMemBase = reinterpret_cast<uint64_t>(ScratchpadMemory);
  UPDOWN_INFOMSG("SPMemBase and UDbase changed to 0x%lX",
                 this->MachineConfig.SPMemBase);
  this->MachineConfig.ControlBase = reinterpret_cast<uint64_t>(ControlMemory);
  UPDOWN_INFOMSG("ControlBase changed to 0x%lX",
                 this->MachineConfig.ControlBase);
  // ReInit Memory Manager with new machine configuration
  reset_memory_manager();
}

void SimUDRuntime_t::initPythonInterface(EmulatorLogLevel printLevel,
                                         bool perf_log_enable,
                                         bool perf_log_internal_enable) {

  Py_Initialize();
  #ifdef ASST_FASTSIM
  total_uds = this->MachineConfig.NumStacks *
              this->MachineConfig.NumUDs;
  #else
  total_uds = this->MachineConfig.NumNodes * this->MachineConfig.NumStacks *
              this->MachineConfig.NumUDs;
  #endif
  upstream_pyintf = new Upstream_PyIntf *[total_uds];

#ifdef ASST_FASTSIM
  for (uint32_t node = 0; node < 1; node++) {
#else
  for (uint32_t node = 0; node < this->MachineConfig.NumNodes; node++) {
#endif
    for (uint32_t stack = 0; stack < this->MachineConfig.NumStacks; stack++) {
      for (uint32_t udid = 0; udid < this->MachineConfig.NumUDs; udid++) {
        uint32_t ud_idx = (node * this->MachineConfig.NumStacks + stack) *
                              this->MachineConfig.NumUDs +
                          udid;
        uint32_t nwid = ((node << 11) & 0x07FFF800) | ((stack << 8) & 0x00000700) |
                  ((udid << 6) & 0x000000C0);
        
        uint64_t spBase = this->MachineConfig.SPMemBase + ((node * this->MachineConfig.NumStacks + stack) * this->MachineConfig.NumUDs + udid) * this->MachineConfig.NumLanes * this->MachineConfig.SPBankSize;
        UPDOWN_INFOMSG("Creating UpDown: Node: %d, Stack: %d, UD: %d, nwid: %d ud_idx = %d\n",
      node, stack, udid, nwid, ud_idx);
        upstream_pyintf[ud_idx] = new Upstream_PyIntf(
            nwid, ud_idx, this->MachineConfig.NumLanes, programFile, programName,
            simulationDir, this->MachineConfig.LocalMemAddrMode,
            this->MachineConfig.SPBankSize, spBase, LogFileName, 10000000000,
            printLevel, 0, perf_log_enable, perf_log_internal_enable);
      }
    }
  }

  // Get UPDOWN_SIM_ITERATIONS from env variable
  if (char *EnvStr = getenv("UPDOWN_SIM_ITERATIONS"))
    max_sim_iterations = std::stoi(EnvStr);
  UPDOWN_INFOMSG("Running with UPDOWN_SIM_ITERATIONS = %ld",
                 max_sim_iterations);

  // This creates a set of files used to communicate with the python word
  // Each lane must have a file. The emulator class uses the same files to
  // read and write data.
  UPDOWN_INFOMSG("total uds:%d\n", total_uds);
  int *fd = new int[total_uds];

  sendmap = new uint32_t *[total_uds];
  for (unsigned int j = 0; j < total_uds; j++) {
    int fdnum = j;
    UPDOWN_INFOMSG("fdnum:%d\n", fdnum);
    fd[fdnum] = -1;
    std::string file_name = "./ud" + std::to_string(j) + "_send.txt";
    if ((fd[fdnum] = open(file_name.c_str(), O_RDWR, 0)) == -1) {
      UPDOWN_ERROR("unable to open %s", file_name.c_str());
      exit(EXIT_FAILURE);
    }
    sendmap[j] = (uint32_t *)mmap(
        NULL /*addr*/, 8 * 262144 * sizeof(uint32_t) /*lenght*/,
        PROT_READ | PROT_WRITE /*prot*/, MAP_SHARED /*flags*/,
        fd[fdnum] /*file_descriptor*/, 0 /*offset*/);

    if (sendmap[j] == MAP_FAILED) {
      UPDOWN_ERROR("SendMap Failed");
      exit(EXIT_FAILURE);
    }
    upstream_pyintf[j]->set_print_level(printLevel);
  }

  delete[] fd;
}

void SimUDRuntime_t::init_stats() {
  uint64_t upperLimit = this->MachineConfig.NumUDs * this->MachineConfig.NumStacks;
  #ifndef ASST_FASTSIM
    upperLimit *= this->MachineConfig.NumNodes;
  #endif

  for (uint64_t ud_id=0; ud_id<upperLimit; ++ud_id) {
    for (uint64_t lane_num=0; lane_num<this->MachineConfig.NumLanes; ++lane_num) {
      this->simStats[ud_id][lane_num].cur_num_sends = 0;
      this->simStats[ud_id][lane_num].num_sends = 0;
      this->simStats[ud_id][lane_num].exec_cycles = 0;
      this->simStats[ud_id][lane_num].idle_cycles = 0;
      this->simStats[ud_id][lane_num].lm_write_bytes = 0;
      this->simStats[ud_id][lane_num].lm_read_bytes = 0;
      this->simStats[ud_id][lane_num].transition_cnt = 0;
      this->simStats[ud_id][lane_num].total_inst_cnt = 0;
      this->simStats[ud_id][lane_num].send_inst_cnt = 0;
      this->simStats[ud_id][lane_num].move_inst_cnt = 0;
      this->simStats[ud_id][lane_num].branch_inst_cnt = 0;
      this->simStats[ud_id][lane_num].alu_inst_cnt = 0;
      this->simStats[ud_id][lane_num].yield_inst_cnt = 0;
      this->simStats[ud_id][lane_num].compare_inst_cnt = 0;
      this->simStats[ud_id][lane_num].cmp_swp_inst_cnt = 0;
      this->simStats[ud_id][lane_num].event_queue_max = 0;
      this->simStats[ud_id][lane_num].event_queue_mean = 0.0;
      this->simStats[ud_id][lane_num].operand_queue_max = 0;
      this->simStats[ud_id][lane_num].operand_queue_mean = 0.0;
      for (uint64_t i=0; i<16; ++i) {
        this->simStats[ud_id][lane_num].user_counter[i] += 0;
      }
    }
  }
}

void SimUDRuntime_t::send_event(event_t ev) {
  // Perform the regular access. This will have no effect
  UDRuntime_t::send_event(ev);
  if (!python_enabled)
    return;
  auto netid = ev.get_NetworkId();
  uint32_t udid = this->get_globalUDNum((netid));
  if (ev.get_NumOperands() != 0) {
    for (uint8_t i = 0; i < ev.get_NumOperands() + 1; i++)
      upstream_pyintf[udid]->insert_operand(ev.get_OperandsData()[i],
                                            (ev.get_NetworkId()).get_LaneId());
  } else {
    upstream_pyintf[udid]->insert_operand(0, (ev.get_NetworkId()).get_LaneId());
  }
  upstream_pyintf[udid]->insert_event(ev.get_EventWord(), ev.get_NumOperands(),
                                      (ev.get_NetworkId()).get_LaneId());
}

void SimUDRuntime_t::executeSingleLane(uint8_t ud_id, uint8_t lane_num) {
  UPDOWN_INFOMSG("Executing a new event in lane %d. events left = %d", lane_num,
                 upstream_pyintf[ud_id]->getEventQ_Size(lane_num));
  struct SimStats local_stats;
  int exec_state = upstream_pyintf[ud_id]->execute(0, local_stats, lane_num, 0);
  update_stats(local_stats, ud_id, lane_num);
  UPDOWN_INFOMSG(
      "C++ Process executed python process - Returned %d - events left %d",
      exec_state, upstream_pyintf[ud_id]->getEventQ_Size(lane_num));

  // Execution_state is useful for messages to communicate with memory.
  // exec_state is:
  //   -1    -> Yeld terminate
  //   0     -> Yeld without messages to send
  //   N > 0 -> Yeld with N messages to send. (N also available in
  //   sendmap[lane][0] below)
  uint32_t numsend = sendmap[ud_id][0];
  if (exec_state > 0 || ((exec_state == -1) && (numsend > 0))) {
    UPDOWN_INFOMSG("Lane: %d Messages to be sent - numMessages :%d", lane_num,
                   numsend);

    // Variable to manage the offset within the sendmap memory mapped file
    int offset = 1;

    // send out requests to memory for the size specified
    for (int i = 0; i < numsend; i++) {
      uint32_t lane_id;  // Lane ID for continuation
      uint32_t node_id;  // Lane ID for continuation
      uint32_t stack_id; // Lane ID for continuation
      uint32_t ud_num;   // Lane ID for continuation
      uint64_t sevent;   // Dest Event
      uint64_t sdest;    // Dest Addr / Lane Num
      uint64_t scont;    // Continuation Word
      uint32_t ssize;    // Size in bytes
      uint32_t smode_0;  // Mode - lane/mem
      uint32_t smode_1;  // Mode - return to same lane?
      uint32_t smode_2;  // Mode - load/store

      uint32_t mode = sendmap[ud_id][offset++];
      smode_0 = (mode & 0x1);
      smode_1 = (mode & 0x2) >> 1;
      smode_2 = (mode & 0x4) >> 2;
      UPDOWN_INFOMSG("Send Mode: mode:%d, 0:%d, 1:%d, 2:%d", mode, smode_0,
                     smode_1, smode_2);

      uint32_t sm_cycle = sendmap[ud_id][offset++]; //[8*i+2]; Not used here
      uint64_t temp_val = 0;
      sevent = sendmap[ud_id][offset++] & 0xffffffff; //[8*i+3];
      temp_val = sendmap[ud_id][offset++];
      sevent = sevent | ((temp_val << 32) & 0xffffffff00000000); //[8*i+3];

      // Depending on smode_0, we determine the direction of the memory access
      if (smode_0 == 0) { // DRAM Memory bound
        // Destination address is split in two since the UpDown address space
        // is 32 bits
        uint64_t lower = sendmap[ud_id][offset++]; //[8*i+5];
        uint64_t upper = sendmap[ud_id][offset++]; //[8*i+4];
        sdest = (lower & 0xffffffff) | ((upper << 32) & 0xffffffff00000000);
        UPDOWN_INFOMSG("Memory Bound Load: %d, Store: %d", !smode_2, smode_2);
        UPDOWN_INFOMSG("Send Dest: 0x%lX, Upper: 0x%lX, Lower: 0x%lX", sdest,
                       upper, lower);
      } else { // Scratchpad Memory Bound to another lane
        uint64_t lower = sendmap[ud_id][offset++]; //[8*i+5];
        uint64_t upper = sendmap[ud_id][offset++]; //[8*i+4];
        sdest = (lower & 0xffffffff) | ((upper << 32) & 0xffffffff00000000);
        UPDOWN_INFOMSG("Send Network ID: 0x%lx ", sdest);
      }

      // Get continuation and size
      temp_val = 0;
      scont = sendmap[ud_id][offset++] & 0xffffffff; //[8*i+3];
      temp_val = sendmap[ud_id][offset++];
      scont = scont | ((temp_val << 32) & 0xffffffff00000000); //[8*i+3];
      ssize = sendmap[ud_id][offset++];                        //[8*i+7];
      UPDOWN_INFOMSG("Send Cont: %lu, Size: %d", scont, ssize);
      uint8_t sdata[ssize];
      uint64_t sdata_64[ssize / 8];

      // Obtain the data to be sent
      if (smode_0 == 1) {
        UPDOWN_INFOMSG("Send data to networkid: %lu, Size:%d", sdest, ssize);
        for (int j = 0; j < ssize / 8; j++) {
          temp_val = 0;
          sdata_64[j] = sendmap[ud_id][offset++] & 0xffffffff; //[8*i+8+j];
          temp_val = sendmap[ud_id][offset++];
          sdata_64[j] =
              sdata_64[j] | ((temp_val << 32) & 0xffffffff00000000); //[8*i+3];
          UPDOWN_INFOMSG("data[%d]: %ld", j, sdata_64[j]);
        }
      }
      // Store operation
      if (smode_2 == 1) {
        for (int j = 0; j < ssize; j += 8) {
          sdata[j] =
              (uint8_t)(sendmap[ud_id][offset] & 0xff); //[8*i+8+(j/4)] & 0xff);
          sdata[j + 1] = (uint8_t)((sendmap[ud_id][offset] & 0xff00) >> 8);
          sdata[j + 2] = (uint8_t)((sendmap[ud_id][offset] & 0xff0000) >> 16);
          sdata[j + 3] = (uint8_t)((sendmap[ud_id][offset] & 0xff000000) >> 24);
          offset++;
          sdata[j + 4] = (uint8_t)(sendmap[ud_id][offset] & 0xff);
          sdata[j + 5] = (uint8_t)((sendmap[ud_id][offset] & 0xff00) >> 8);
          sdata[j + 6] = (uint8_t)((sendmap[ud_id][offset] & 0xff0000) >> 16);
          sdata[j + 7] = (uint8_t)((sendmap[ud_id][offset] & 0xff000000) >> 24);
          offset++;
          UPDOWN_INFOMSG(
              "Send Data[0]: %d, Data:[1]: %d, Data[2]: %d, Data[3]: %d \
              Data[4]: %d, Data:[5]: %d, Data[6]: %d, Data[7]: %d",
              sdata[j], sdata[j + 1], sdata[j + 2], sdata[j + 3], sdata[j + 4],
              sdata[j + 5], sdata[j + 6], sdata[j + 7]);
        }
      }
      // The continuation Lane ID
      uint32_t send_policy = (scont & 0x3000000000000000) >> 60;
      node_id = (scont & 0xFFFF00000000000) >> 44;
      stack_id = (scont & 0xF0000000000) >> 40;
      ud_num = (scont & 0xC000000000) >> 38;
      lane_id = (scont & 0x3f00000000) >> 32;
      UPDOWN_INFOMSG("Send LaneID:%d", lane_id);
      uint32_t cont_ud_id = node_id * (this->MachineConfig.NumStacks *
                                       this->MachineConfig.NumUDs) +
                            stack_id * (this->MachineConfig.NumUDs) + ud_num;

      if (!smode_0) { // memory bound messages
        // TODO: Send message to memory
        if (!smode_2) {
          // Loads
          UPDOWN_INFOMSG("Loading from Mapped Memory address: 0x%lX, size: %d",
                         sdest, ssize);

          ptr_t src = reinterpret_cast<ptr_t>(sdest);
          ptr_t dst = reinterpret_cast<ptr_t>(sdata);
          std::memcpy(dst, src, ssize);
          uint64_t edata = 0;
          uint64_t noupdate_cont = 0x7fffffffffffffff;
          // Andronicus to continue from here
          upstream_pyintf[cont_ud_id]->insert_operand(
              noupdate_cont, lane_id); // Insert continuation first!
          for (int i = 0; i < ssize / 8; i++) {
            edata = (((static_cast<uint64_t>(sdata[8 * i + 7] & 0xff) << 56) &
                      0xff00000000000000) |
                     ((static_cast<uint64_t>(sdata[8 * i + 6] & 0xff) << 48) &
                      0x00ff000000000000) |
                     ((static_cast<uint64_t>(sdata[8 * i + 5] & 0xff) << 40) &
                      0x0000ff0000000000) |
                     ((static_cast<uint64_t>(sdata[8 * i + 4] & 0xff) << 32) &
                      0x000000ff00000000) |
                     ((static_cast<uint64_t>(sdata[8 * i + 3] & 0xff) << 24) &
                      0x00000000ff000000) |
                     ((static_cast<uint64_t>(sdata[8 * i + 2] & 0xff) << 16) &
                      0x0000000000ff0000) |
                     ((static_cast<uint64_t>(sdata[8 * i + 1] & 0xff) << 8) &
                      0x000000000000ff00) |
                     ((static_cast<uint64_t>(sdata[8 * i] & 0xff)) &
                      0x00000000000000ff));
            UPDOWN_INFOMSG("edata[%d]:%ld", i, edata);
            upstream_pyintf[cont_ud_id]->insert_operand(edata, lane_id);
          }
          upstream_pyintf[cont_ud_id]->insert_operand(
              sdest, lane_id); // Address updated
          upstream_pyintf[cont_ud_id]->insert_event(scont, (ssize / 8) + 1,
                                                    lane_id);

        } else {
          // Stores
          UPDOWN_INFOMSG("Storing to Mapped Memory address: 0x%lX, size: %d",
                         sdest, ssize);

          ptr_t src = reinterpret_cast<ptr_t>(sdata);
          ptr_t dst = reinterpret_cast<ptr_t>(sdest);
          std::memcpy(dst, src, ssize);

          uint64_t noupdate_cont = 0x7fffffffffffffff;
          upstream_pyintf[cont_ud_id]->insert_operand(
              noupdate_cont, lane_id); // Insert continuation first!
          upstream_pyintf[cont_ud_id]->insert_operand(
              sdest, lane_id); // Update empty operand
          upstream_pyintf[cont_ud_id]->insert_operand(
              sdest, lane_id); // Empty operands
          upstream_pyintf[cont_ud_id]->insert_event(scont, 2, lane_id);
        }
      } else {
        // Sending message to another lane
        send_policy = (sdest & 0x3800000) >> 27;
        node_id = (sdest & 0x7FF800) >> 11;
        stack_id = (sdest & 0x700) >> 8;
        ud_num = (sdest & 0x0C0) >> 6;
        lane_id = (sdest & 0x03f);

        uint32_t dest_ud_id = node_id * (this->MachineConfig.NumStacks *
                                         this->MachineConfig.NumUDs) +
                              stack_id * (this->MachineConfig.NumUDs) + ud_num;
        UPDOWN_INFOMSG("Send Dest UD ID:%d", dest_ud_id);
        UPDOWN_INFOMSG("Send Policy:%d", send_policy);
        if (send_policy != 0)
          lane_id =
              upstream_pyintf[dest_ud_id]->getPolicyLane(lane_id, send_policy);
        UPDOWN_INFOMSG("Send LaneID:%d", lane_id);

        upstream_pyintf[dest_ud_id]->insert_operand(
            scont,
            lane_id); // insert continuation first
        UPDOWN_INFOMSG("LaneNum: %ld, OB[0]: %ld (0x%lX)", sdest, scont, scont);
        for (int i = 0; i < ssize / 8; i++) {
          upstream_pyintf[dest_ud_id]->insert_operand(
              sdata_64[i], lane_id); // insert all collected operands
          UPDOWN_INFOMSG("LaneNum:%ld, OB[%d]: %ld (0x%lX)", sdest, i + 1,
                         sdata_64[i], sdata_64[i]);
        }
        upstream_pyintf[dest_ud_id]->insert_event(
            sevent, ssize / 8,
            lane_id); // insert the event
      }
    }
  }
  if (exec_state == -1) {
    UPDOWN_INFOMSG("Lane: %d Yielded and Terminated - Writing result now",
                   lane_num);
  }
}

void SimUDRuntime_t::start_exec(networkid_t nwid) {
  // Perform the regular access. This will have no effect
  UDRuntime_t::start_exec(nwid);
  if (!python_enabled)
    return;
#ifdef ASST_FASTSIM
  uint32_t total_uds = this->MachineConfig.NumStacks *
                       this->MachineConfig.NumUDs;
#else
  uint32_t total_uds = this->MachineConfig.NumNodes *
                       this->MachineConfig.NumStacks *
                       this->MachineConfig.NumUDs;
#endif
  // Then we do a round robin execution of all the lanes while
  // there is something executing
  bool something_exec;
  uint64_t num_iterations = 0;
  do {
    something_exec = false;
    for (int ud = 0; ud < total_uds; ud++) {
      for (int ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
        if (upstream_pyintf[ud]->getEventQ_Size(ln) > 0) {
          UPDOWN_INFOMSG("Dumping Event Queue of lane %d", ln);
          upstream_pyintf[ud]->dumpEventQueue(ln);
          something_exec = true;
          executeSingleLane(ud, ln);
        }
      }
    }
  } while (something_exec &&
           (!max_sim_iterations || ++num_iterations < max_sim_iterations));
}

void SimUDRuntime_t::t2ud_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset) {
  UDRuntime_t::t2ud_memcpy(data, size, nwid, offset);
  uint32_t ud_num = this->get_globalUDNum(nwid);
  if (!python_enabled)
    return;
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset) -
                  UDRuntime_t::get_ud_physical_memory(nwid);
  ptr_t data_ptr = reinterpret_cast<word_t *>(data);
  for (int i = 0; i < size / sizeof(word_t); i++) {
    // Address is local
    upstream_pyintf[ud_num]->insert_scratch(addr, *data_ptr);
    addr += sizeof(word_t);
    data_ptr++;
  }
}

void SimUDRuntime_t::ud2t_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset) {
  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset) -
                  UDRuntime_t::get_ud_physical_memory(nwid);
  uint64_t apply_offset = UDRuntime_t::get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  ptr_t base = BaseAddrs.spaddr + apply_offset;
  UPDOWN_INFOMSG("Actual addr: 0x%lX , base: 0x%lX", addr, (unsigned long)base);
  UPDOWN_ASSERT(
      base + size / sizeof(word_t) <
          BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
      "ud2t_memcpy: memory access to 0x%lX out of scratchpad memory bounds "
      "with offset %lu bytes and size %lu bytes. Scratchpad memory Base "
      "Address 0x%lX scratchpad memory size %lu bytes",
      (unsigned long)(base), (unsigned long)(apply_offset * sizeof(word_t)),
      (unsigned long)size, (unsigned long)BaseAddrs.spaddr,
      (unsigned long)MachineConfig.SPSize());
  if (python_enabled)
    upstream_pyintf[ud_num]->read_scratch(
        addr, reinterpret_cast<uint8_t *>(base), size);
  UDRuntime_t::ud2t_memcpy(data, size, nwid, offset);
}

bool SimUDRuntime_t::test_addr(networkid_t nwid, uint32_t offset,
                               word_t expected) {
  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset) -
                  UDRuntime_t::get_ud_physical_memory(nwid);
  uint64_t apply_offset = UDRuntime_t::get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  ptr_t base = BaseAddrs.spaddr + apply_offset;
  UPDOWN_ASSERT(
      base < BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
      "test_addr: memory access to 0x%lX out of scratchpad memory bounds "
      "with offset %lu bytes and size 4 bytes. Scratchpad memory Base Address "
      "0x%lX scratchpad memory size %lu bytes",
      (unsigned long)(base), (unsigned long)(apply_offset * sizeof(word_t)),
      (unsigned long)BaseAddrs.spaddr, (unsigned long)MachineConfig.SPSize());

  if (python_enabled) {
    start_exec(nwid);
    upstream_pyintf[ud_num]->read_scratch(
        addr, reinterpret_cast<uint8_t *>(base), sizeof(word_t));
  }
  return UDRuntime_t::test_addr(nwid, offset, expected);
}

void SimUDRuntime_t::test_wait_addr(networkid_t nwid, uint32_t offset,
                                    word_t expected) {

  while (!test_addr(nwid, offset, expected))
    ;
  // The bottom call will never hold since we're holding here
  UDRuntime_t::test_wait_addr(nwid, offset, expected);
}

void SimUDRuntime_t::update_stats(struct SimStats &loc_stats, uint32_t ud_id,
                                  uint8_t lane_num) {
  this->simStats[ud_id][lane_num].cur_num_sends = loc_stats.cur_num_sends;
  this->simStats[ud_id][lane_num].num_sends += loc_stats.num_sends;
  this->simStats[ud_id][lane_num].exec_cycles += loc_stats.exec_cycles;
  this->simStats[ud_id][lane_num].idle_cycles += loc_stats.idle_cycles;
  this->simStats[ud_id][lane_num].lm_write_bytes += loc_stats.lm_write_bytes;
  this->simStats[ud_id][lane_num].lm_read_bytes += loc_stats.lm_read_bytes;
  this->simStats[ud_id][lane_num].transition_cnt += loc_stats.transition_cnt;
  this->simStats[ud_id][lane_num].total_inst_cnt += loc_stats.total_inst_cnt;
  this->simStats[ud_id][lane_num].send_inst_cnt += loc_stats.send_inst_cnt;
  this->simStats[ud_id][lane_num].move_inst_cnt += loc_stats.move_inst_cnt;
  this->simStats[ud_id][lane_num].branch_inst_cnt += loc_stats.branch_inst_cnt;
  this->simStats[ud_id][lane_num].alu_inst_cnt += loc_stats.alu_inst_cnt;
  this->simStats[ud_id][lane_num].yield_inst_cnt += loc_stats.yield_inst_cnt;
  this->simStats[ud_id][lane_num].compare_inst_cnt +=
      loc_stats.compare_inst_cnt;
  this->simStats[ud_id][lane_num].cmp_swp_inst_cnt +=
      loc_stats.cmp_swp_inst_cnt;
  this->simStats[ud_id][lane_num].event_queue_max = loc_stats.event_queue_max;
  this->simStats[ud_id][lane_num].event_queue_mean = loc_stats.event_queue_mean;
  this->simStats[ud_id][lane_num].operand_queue_max =
      loc_stats.operand_queue_max;
  this->simStats[ud_id][lane_num].operand_queue_mean =
      loc_stats.operand_queue_mean;
  for (int i = 0; i < 16; i++) {
    this->simStats[ud_id][lane_num].user_counter[i] +=
        loc_stats.user_counter[i];
  }
}

void SimUDRuntime_t::print_stats(uint32_t ud_id, uint8_t lane_num) {
  const int wid = 10;
  std::printf("[UD%d-L%d] num_sends           = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].num_sends);
  std::printf("[UD%d-L%d] exec_cycles         = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].exec_cycles);
  std::printf("[UD%d-L%d] idle_cycles         = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].idle_cycles);
  std::printf("[UD%d-L%d] lm_write_bytes      = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].lm_write_bytes);
  std::printf("[UD%d-L%d] lm_read_bytes       = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].lm_read_bytes);
  std::printf("[UD%d-L%d] transition_cnt      = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].transition_cnt);
  std::printf("[UD%d-L%d] total_inst_cnt      = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].total_inst_cnt);
  std::printf("[UD%d-L%d] send_inst_cnt       = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].send_inst_cnt);
  std::printf("[UD%d-L%d] move_inst_cnt       = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].move_inst_cnt);
  std::printf("[UD%d-L%d] branch_inst_cnt     = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].branch_inst_cnt);
  std::printf("[UD%d-L%d] alu_inst_cnt        = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].alu_inst_cnt);
  std::printf("[UD%d-L%d] yield_inst_cnt      = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].yield_inst_cnt);
  std::printf("[UD%d-L%d] compare_inst_cnt    = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].compare_inst_cnt);
  std::printf("[UD%d-L%d] cmp_swp_inst_cnt    = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].cmp_swp_inst_cnt);
  std::printf("[UD%d-L%d] event_queue_max     = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].event_queue_max);
  std::printf("[UD%d-L%d] event_queue_mean    = %*.2lf\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].event_queue_mean);
  std::printf("[UD%d-L%d] operand_queue_max   = %*lu\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].operand_queue_max);
  std::printf("[UD%d-L%d] operand_queue_mean  = %*.2lf\n", ud_id, lane_num, wid,
              this->simStats[ud_id][lane_num].operand_queue_mean);
  for (int i = 0; i < 16; i++) {
    std::printf("[UD%d-L%d] user_counter%2d      = %*ld\n", ud_id, lane_num, i,
                wid, this->simStats[ud_id][lane_num].user_counter[i]);
  }
}

SimUDRuntime_t::~SimUDRuntime_t() {
  // delete[] MappedMemory;
  delete[] ScratchpadMemory;
  munmap(MappedMemory, this->MachineConfig.MapMemSize);
//   munmap(ScratchpadMemory, this->MachineConfig.SPSize());
  delete[] GMappedMemory;
  delete[] ControlMemory;
  if (!python_enabled)
    return;
  // remove temp files for python communication
  #ifdef ASST_FASTSIM
  uint32_t total_uds =
      MachineConfig.NumStacks * MachineConfig.NumUDs;
  #else
  uint32_t total_uds =
      MachineConfig.NumNodes * MachineConfig.NumStacks * MachineConfig.NumUDs;
  #endif
  for (unsigned int j = 0; j < total_uds; j++) {
    std::string file_name = "./ud" + std::to_string(j) + "_send.txt";
    UPDOWN_INFOMSG("Removing file %s", file_name.c_str());
    if (remove(file_name.c_str()) != 0) {
      UPDOWN_ERROR("unable to remove file %s", file_name.c_str());
    }
    delete upstream_pyintf[j];
  }
  //delete[] upstream_pyintf;
  delete[] sendmap;
  Py_Finalize();
}
} // namespace UpDown
