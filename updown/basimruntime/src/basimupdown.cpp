#include "basimupdown.h"
#include "debug.h"
#include "memorySegments.h"
#include "networkid.h"
#include "basim_stats.hh"
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <ios>
#include <string>
#include <sys/mman.h>
#include <sys/types.h>
#include <utility>
#include <vector>
#include <omp.h>
#include "types.hh"
#include "lanetypes.hh"
#include "fstream"
#include "logging.hh"
#include "updown_config.h"
#include "util.hh"
#include "mmessage.hh"

namespace UpDown {

/*
  This is a hack as it is possible to have multiple instances of the runtime,
  but only one global logger is allowed. We need to know we are logging from
  which runtime instance.
*/
BASimUDRuntime_t *curRuntimeInstance = nullptr;

  /**
   * @brief Construct a new BASimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. Python will be disabled. Only simulating memory interactions.
   *
   */
BASimUDRuntime_t::BASimUDRuntime_t() : SimUDRuntime_t() {
    UPDOWN_INFOMSG("Initializing BASimulated Runtime with default params");
    UPDOWN_WARNING("No python program. Python will be disabled, only "
                   "simulating memory interactions");
    initialize(32, 1, 1);
}

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
BASimUDRuntime_t::BASimUDRuntime_t(ud_machine_t machineConfig)
      : SimUDRuntime_t(machineConfig){
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_WARNING("No python program. Python will be disabled, only "
                   "simulating memory interactions");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    
    initialize(32, this->MachineConfig.NumNodes, 1);
  }

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
BASimUDRuntime_t::BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile,
                 std::string programName, basim::Addr pgbase, uint32_t numTicks)
      : SimUDRuntime_t(machineConfig ,programFile, programName), NumTicks(numTicks)
        {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    UPDOWN_INFOMSG("Running file %s Program %s", programFile.c_str(),
                   programName.c_str());

    initialize(32, this->MachineConfig.NumNodes, 1);
    initMachine(programFile, pgbase);
    calc_addrmap();
    init_stats();
    initLogs(std::filesystem::path(programFile + std::to_string(nodeID) + ".logs").filename());
    initOMP();
}


BASimUDRuntime_t::BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile, basim::Addr pgbase, 
                    uint32_t numTicks, std::string log_subfolder_name) 
                    : SimUDRuntime_t(machineConfig, programFile), NumTicks(numTicks) {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    UPDOWN_INFOMSG("Running file %s Program %s", programFile.c_str(), programName.c_str());

    initialize(32, this->MachineConfig.NumNodes, 1);
    initMachine(programFile, pgbase);
    calc_addrmap();
    init_stats();
    initLogs(std::filesystem::path(programFile + ".logs") / std::filesystem::path(log_subfolder_name));
    initOMP();
  }

BASimUDRuntime_t::BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile, basim::Addr pgbase,
            uint64_t nnodes, uint64_t nodeID, uint64_t numUDperNode, uint64_t top_per_node, uint32_t numTicks,
            std::string log_subfolder_name) : SimUDRuntime_t(machineConfig, programFile), NumTicks(numTicks) {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    UPDOWN_INFOMSG("Running file %s Program %s", programFile.c_str(), programName.c_str());

    initialize(numUDperNode, nnodes, top_per_node);
    this->nodeID = nodeID;
    
    initMachine(programFile, pgbase);
    calc_addrmap();
    init_stats();
    initLogs(std::filesystem::path(programFile + ".logs") / std::filesystem::path(log_subfolder_name));
    initOMP();
}

void BASimUDRuntime_t::initialize(uint64_t numUDperNode, uint64_t nnodes, uint64_t topPerNode) {
    #ifdef ASST_FASTSIM
        for (uint64_t i = 0; i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks; i++) {
            std::vector<struct BASimStats> v(this->MachineConfig.NumLanes);
            this->simStats.push_back(v);
        }

        std::vector<struct BASimNodeStats> v(nnodes);
        this->simNodeStats.push_back(v);

        this->nnodes = nnodes;
        this->numUDperNode = numUDperNode;
        pthread_mutex_init(&mutex, nullptr);
        pthread_mutex_init(&top_lock, nullptr);
        pthread_cond_init(&condStart, nullptr);
        pthread_cond_init(&condTest, nullptr);
        sem_init(&semStart, 0, 0);
        set_status(0);
        nnodes_end = 0;
        // initialize message_list
        receive_message_queue = new basim::Buffer<std::unique_ptr<basim::MMessage> >(0);
        for(int i=0; i<this->numUDperNode; i++) 
            send_message_queue[i] = new basim::Buffer<std::unique_ptr<basim::MMessage> >(0); 
    #else
        for(uint64_t i = 0; i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes; i++) {
            std::vector<struct BASimStats> v(this->MachineConfig.NumLanes);
            this->simStats.push_back(v);
        }

        for(uint64_t i=0; i<this->MachineConfig.NumNodes; ++i) {
            struct BASimNodeStats stats;
            stats.reset(this->MachineConfig.NumNodes);
            this->simNodeStats.push_back(stats);
        }

        this->nnodes = 1;
    #endif
    nodeID = 0;
    python_enabled = false;
    send_event_valid = 0;
    this->topPerNode = topPerNode;
    barrier_times = this->nnodes*this->topPerNode;
    set_barrier_times(barrier_times);
    
    this->startTime = std::chrono::high_resolution_clock::now();
    UpDown::curRuntimeInstance = this;
    
    pthread_mutex_init(&map_lock, nullptr);
    thread_num.store(0, std::memory_order_release);
    test_nwid = new networkid_t[this->topPerNode];
    test_offset = new uint32_t[this->topPerNode];
    test_expected = new word_t[this->topPerNode];
    #ifdef ASST_FASTSIM
        semSync = new sem_t[this->topPerNode];
        for(int i=0; i<this->topPerNode; i++)
            sem_init(&semSync[i], 0, 0);
        semTest = new sem_t[this->topPerNode];
        for(int i=0; i<this->topPerNode; i++)
            sem_init(&semTest[i], 0, 0);
        test_addr_flag = new int[this->topPerNode];
        for(int i=0; i<this->topPerNode; i++)
            test_addr_flag[i]=0;
    #endif
    std::srand(0);
}

void BASimUDRuntime_t::extractSymbols(std::string progfile){
  std::ifstream instream(progfile.c_str(), std::ifstream::binary);
  uint64_t startofEventSymbols;
  uint32_t numEventSymbols, label, labelAddr;
  if(instream){
    instream.seekg(0, instream.end); 
    int length = instream.tellg();
    UPDOWN_INFOMSG("Program Size: %d Bytes", length);
    instream.seekg(0, instream.beg);
    instream.read(reinterpret_cast<char *>(&startofEventSymbols), sizeof(startofEventSymbols));
    instream.seekg(startofEventSymbols, instream.beg);
    instream.read(reinterpret_cast<char *>(&numEventSymbols), sizeof(numEventSymbols));
    UPDOWN_INFOMSG("Extracting %d EventLabels:Addresses from %s", numEventSymbols, progfile.c_str());
    for(auto i = 0; i < numEventSymbols; i++){
      instream.read(reinterpret_cast<char *>(&label), sizeof(label));
      instream.read(reinterpret_cast<char *>(&labelAddr), sizeof(labelAddr));
      symbolMap[label] = labelAddr; 
      UPDOWN_INFOMSG("%d:%d", label, labelAddr);
    }
    instream.seekg(0, instream.beg);
  }else
    UPDOWN_ERROR("Could not load the binary: %s\n", progfile.c_str());
}

void BASimUDRuntime_t::initMachine(std::string progfile, basim::Addr _pgbase){
  globalTick = 0;
  simTicks = 0;
  #ifdef ASST_FASTSIM
  total_uds = this->MachineConfig.NumStacks * this->MachineConfig.NumUDs;
  #else
  total_uds = this->MachineConfig.NumNodes * this->MachineConfig.NumStacks * this->MachineConfig.NumUDs;
  #endif
  uds.reserve(total_uds);

  // Create the default private segment, i.e., the entire memory mapped region
  private_segment_t default_segment(this->MachineConfig.MapMemBase, 
    this->MachineConfig.MapMemBase + this->MachineConfig.MapMemSize, this->MachineConfig.MapMemBase, 0b11);

#ifdef ASST_FASTSIM
  for (uint32_t node = 0; node < 1; node++) 
#else
  for (uint32_t node = 0; node < this->MachineConfig.NumNodes; node++) 
#endif
  {
    basim::UDMemoryPtr udmptr = new basim::UDMemory(node, this->MachineConfig.NumStacks, this->MachineConfig.MemLatency, this->MachineConfig.MemBandwidth, this->MachineConfig.InterNodeLatency + this->MachineConfig.FarMemExtraLatency);
    udMems.push_back(udmptr);

    for (uint32_t stack = 0; stack < this->MachineConfig.NumStacks; stack++) {
      for (uint32_t udid = 0; udid < this->MachineConfig.NumUDs; udid++) {
        uint32_t ud_idx = (node * this->MachineConfig.NumStacks + stack) *
                              this->MachineConfig.NumUDs +
                          udid;
        uint32_t nwid = ((node << 11) & 0x07FFF800) | ((stack << 8) & 0x00000700) |
                  ((udid << 6) & 0x000000C0);
        #ifdef ASST_FASTSIM
        basim::UDAcceleratorPtr udptr = new basim::UDAccelerator(MachineConfig.NumLanes, nwid + nodeID * 2048, MachineConfig.LocalMemAddrMode, MachineConfig.InterNodeLatency);
        #else
        basim::UDAcceleratorPtr udptr = new basim::UDAccelerator(MachineConfig.NumLanes, nwid, MachineConfig.LocalMemAddrMode, MachineConfig.InterNodeLatency);
        #endif
        uds.push_back(udptr);

        basim::Addr spBase = this->MachineConfig.SPMemBase + ((node * this->MachineConfig.NumStacks + stack) * this->MachineConfig.NumUDs + udid) * this->MachineConfig.NumLanes * this->MachineConfig.SPBankSize;
        
        //uds[ud_idx]->initSetup(_pgbase, progfile, spBase);
        //basim::TranslationMemoryPtr tm = new basim::TranslationMemory(nwid, total_uds, spBase);
        extractSymbols(progfile);
        #ifdef ASST_FASTSIM
            uds[ud_idx]->initSetup(_pgbase, progfile, spBase, total_uds, nnodes);
        #else
            uds[ud_idx]->initSetup(_pgbase, progfile, spBase, total_uds);
        #endif
        // Add the translation for the default private local segment to the UpDown's translation memory
        uds[ud_idx]->insertLocalTrans(default_segment);

        UPDOWN_INFOMSG("Creating UpDown: Node: %d, Stack: %d, UD: %d, nwid: %d ud_idx = %d SPBase: %lx\n", 
        node, stack, udid, nwid, ud_idx, spBase);
      }
    }
  }
  
  // Get UPDOWN_SIM_ITERATIONS from env variable
  if (char *EnvStr = getenv("UPDOWN_SIM_ITERATIONS"))
    max_sim_iterations = std::stoi(EnvStr);
  UPDOWN_INFOMSG("Running with UPDOWN_SIM_ITERATIONS = %ld",
                 max_sim_iterations);

}

void BASimUDRuntime_t::initOMP() {
  #ifndef GEM5_MODE
    // A set environment variable always takes precedence
    if(!getenv("OMP_NUM_THREADS")) {
      uint64_t hardwareThreads = omp_get_max_threads();
      int threads = int(hardwareThreads < total_uds ? hardwareThreads : total_uds);
      omp_set_num_threads(threads);

      UPDOWN_INFOMSG("OMP scheduler: Available hardware threads: %lu, running %d threads in parallel for %u UDs",
                      hardwareThreads, threads, total_uds);
    }
    if(!getenv("OMP_SCHEDULE")) {
      omp_set_schedule(omp_sched_static, 1);
    }
    omp_sched_t kind;
    int chunk_size;
    omp_get_schedule(&kind, &chunk_size);
    std::string kindStr;

    switch(kind) {
      case omp_sched_static:
        kindStr = "static";
        break;
      case omp_sched_dynamic:
        kindStr = "dynamic";
        break;
      case omp_sched_guided:
        kindStr = "guided";
        break;
      case omp_sched_auto:
        kindStr = "auto";
        break;
      default:
        kindStr = "other (implementation specific)";
        break;
    }
    UPDOWN_INFOMSG("OMP scheduler: %s, chunk size: %d", kindStr.c_str(), chunk_size);
  #endif
}

static void writeUpdownBasimPerflog(uint32_t network_id, uint32_t thread_id, // IDs
                             uint32_t event_label,     // event
                             uint32_t inc_exec_cycles, // incremental exec cycles
                             uint64_t total_exec_cycles, // total exec cycles
                             uint32_t msg_id, std::string &msg_str // message
) {
  uint64_t final_tick = UpDown::curRuntimeInstance->getCurTick();
  uint64_t sim_ticks = final_tick;
  double sim_sec = 0.0;
  double host_sec = std::chrono::duration<double>(std::chrono::high_resolution_clock::now() - UpDown::curRuntimeInstance->getStartTime()).count();
  uint64_t lane_exec_ticks = total_exec_cycles;

  basim::globalLogs.perflog.writeUpdown(host_sec, final_tick, sim_ticks, sim_sec, network_id, thread_id, event_label,
               lane_exec_ticks, msg_id, msg_str);
}

static void writeBasimTracelog(uint32_t inc_exec_cycles,  // incremental exec cycles
                               std::string &msg_type_str, // type of message
                               std::string &msg_str       // message
) {
  uint64_t final_tick = UpDown::curRuntimeInstance->getCurTick();
  uint64_t sim_ticks = final_tick;

  basim::globalLogs.tracelog.write(sim_ticks, msg_type_str, msg_str);
}

void BASimUDRuntime_t::initLogs(std::filesystem::path log_folder_path) {
  if (!std::filesystem::exists(log_folder_path)) {
    if (std::filesystem::create_directories(log_folder_path)) {
      UPDOWN_INFOMSG("CREATED LOG FOLDER: %s\n", log_folder_path.c_str());
    } else {
      UPDOWN_ERROR("COULD NOT CREATE LOG FOLDER: %s\n", log_folder_path.c_str());
    }
  } else {
    UPDOWN_INFOMSG("EXISTING LOG FOLDER: %s\n", log_folder_path.c_str());
  }

  // open perflog
  basim::globalLogs.perflog.open(log_folder_path / "perflog.tsv");
  basim::globalLogs.perflog.registerPerflogCallback(writeUpdownBasimPerflog);
  // open tracelog
  basim::globalLogs.tracelog.open(log_folder_path / "tracelog.log");
  basim::globalLogs.tracelog.registerTracelogCallback(writeBasimTracelog);
#if defined (ENABLE_SQLITE)
  char *errMsg = 0;
  std::remove((log_folder_path / "stats.db").c_str());
  auto rc = sqlite3_open((log_folder_path / "stats.db").c_str(), &(this->stats_db));
  if (rc) {
    std::cerr << "Can't open database: " << sqlite3_errmsg(this->stats_db) << std::endl;
  }
  rc = sqlite3_exec(this->stats_db, "PRAGMA journal_mode=WAL;", 0, 0, &errMsg);
  if (rc != SQLITE_OK) {
      std::cerr << "Failed to enable WAL mode: " << errMsg << std::endl;
      sqlite3_free(errMsg);
  }
#endif
}

void BASimUDRuntime_t::send_event(event_t ev) {
  // Perform the regular access. This will have no effect
  UDRuntime_t::send_event(ev);
  send_event_ev = ev;
  send_event_valid = 1;

#ifndef ASST_FASTSIM
  send_event2(send_event_ev);
#endif
}

void BASimUDRuntime_t::send_event2(event_t ev) {
  auto netid = ev.get_NetworkId();
  uint32_t udid = this->get_globalUDNum((netid));

  // Update the label with the actual event label resolved address
  ev.set_EventLabel(symbolMap[ev.get_EventLabel()]);

  basim::eventword_t basimev = basim::EventWord(ev.get_EventWord());
  basim::operands_t op(ev.get_NumOperands(), basim::EventWord(ev.get_OperandsData()[0]));  // num operands + cont
  op.setData(&ev.get_OperandsData()[1]);
  basim::eventoperands_t eops(&basimev, &op);
  sendEventOperands(udid, &eops, (ev.get_NetworkId()).get_LaneId());
  send_event_valid = 0;
}

int BASimUDRuntime_t::getNodeIdx(basim::networkid_t nid){
    return std::ceil(nid.getNodeID()*32.0/numUDperNode);
}

int BASimUDRuntime_t::getUDIdx(basim::networkid_t nid) {
#ifdef ASST_FASTSIM
  return nid.getStackID() * (this->MachineConfig.NumUDs) + nid.getUDID();
#else
  return nid.getNodeID() *
             (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs) +
         nid.getStackID() * (this->MachineConfig.NumUDs) + nid.getUDID();
#endif
}

int BASimUDRuntime_t::getUDIdxForAddr(basim::networkid_t nid, basim::Addr addr, bool isGlobal) {
    #ifdef ASST_FASTSIM
        return nid.getStackID() * (this->MachineConfig.NumUDs) + nid.getUDID();
    #else
        // This needs to be modified when node level DRAM view is available on fastsim
        uint32_t random_number = std::rand() % this->MachineConfig.NumUDs;
        uint32_t node_id = isGlobal ? mapPA2SA(addr, isGlobal).node_id : nid.getNodeID();
        uint32_t stack_id = getMemoryMessageTargetStackID(addr, isGlobal);
        return node_id * (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs) +
          stack_id * (this->MachineConfig.NumUDs) + random_number;
    #endif
}

// uint32_t BASimUDRuntime_t::getMemoryMessageTargetUDNodeID(uint64_t addr) {
//   return ((addr / this->MachineConfig.MemBlockSize) / this->MachineConfig.NumStacks) % this->MachineConfig.NumNodes;
// }

uint32_t BASimUDRuntime_t::getMemoryMessageTargetStackID(uint64_t addr, bool isGlobal) {
    return (addr / this->MachineConfig.MemISegBlockSize) % this->MachineConfig.NumStacks;
}

void BASimUDRuntime_t::postSimulateGem5(uint32_t udid, uint32_t laneID) {
    // Cycle through the send buffers of each lane in the UDs
    while(uds[udid]->sendReady(laneID)){
        std::unique_ptr<basim::MMessage> m = uds[udid]->getSendMessage(laneID);
        switch(m->getType()){
            case basim::MType::M1Type:{
                processMessageM1(std::move(m));
                break;
            }
            case basim::MType::M2Type:{
                processMessageM2(std::move(m), udid);
                break;
            }
            case basim::MType::M3Type:{
                processMessageM3(std::move(m));
                break;
            }
            case basim::MType::M3Type_M:{
                processMessageM3M(std::move(m));
                break;
            }
            case basim::MType::M4Type:{
                processMessageM4(std::move(m));
                break;
            }
            case basim::MType::M4Type_M:{
                processMessageM4M(std::move(m));
                break;
            }
            default:{
                BASIM_ERROR("Undefined Message type in Send Buffer");
                break;
            }
        }
    }
}

void BASimUDRuntime_t::postSimulate(uint32_t udid, uint32_t laneID) {
    // Cycle through the send buffers of each lane in the UDs
    while(uds[udid]->sendReady(laneID)){
        //printf("postSimulate: ud:%d, ln: %d\n", udid, laneID);
        std::unique_ptr<basim::MMessage> m = uds[udid]->getSendMessage(laneID);
         switch(m->getType()){
            case basim::MType::M1Type:{
                uint32_t target_udnodeid = m->getXe().getNWID().getNodeID();
                if (target_udnodeid != (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) {
                    #if defined(FASTSIM_NETWORK_TRACE)
                    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                    "<NODE2NODE, " +
                    std::to_string((udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) +" -> " +
                    std::to_string(target_udnodeid) +", " +
                    std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                    );
                    #endif
                    basim::LaneStats* loc_stats = uds[udid]->getLaneStats(laneID);
                    loc_stats->tran_count_other_node++;
                    loc_stats->tran_bytes_other_node += (m->getLen()+2) * WORDSIZE;

                    uds[udid]->pushDelayedMessage(std::move(m));
                    break;
                }
                processMessageM1(std::move(m));
                break;
            }
            case basim::MType::M2Type:{
                // Writes to memory
                basim::Addr pAddr = m->getdestaddr();
                common_addr sAddr = mapPA2SA(pAddr, m->getIsGlobal());
                uint32_t target_udnodeid;
                uint32_t target_stid;

                target_udnodeid = m->getIsGlobal() ? sAddr.node_id : (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs));
                if (target_udnodeid != (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) {
                    if(m->isStore()){
                      #if defined(FASTSIM_NETWORK_TRACE)
                      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                      "<NODE2DRAM_ST, " +
                      std::to_string((udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) +" -> " +
                      std::to_string(target_udnodeid) +", " +
                      std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                      );
                      #endif

                      basim::LaneStats* loc_stats = uds[udid]->getLaneStats(laneID);
                      loc_stats->dram_store_count_other_node++;
                      loc_stats->dram_store_bytes_other_node += (m->getLen() + 2) * WORDSIZE;

                    }else{
                      #if defined(FASTSIM_NETWORK_TRACE)
                      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                      "<NODE2DRAM_LD, " +
                      std::to_string((udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) +" -> " +
                      std::to_string(target_udnodeid) +", " +
                      std::to_string(2 * WORDSIZE) + "B>"
                      );
                      #endif
                      basim::LaneStats* loc_stats = uds[udid]->getLaneStats(laneID);
                      loc_stats->dram_load_count_other_node++;
                      loc_stats->dram_load_bytes_other_node += 2 * WORDSIZE;
                    }
                    uds[udid]->pushDelayedMessage(std::move(m));
                    break;
                }
                target_stid = this->getMemoryMessageTargetStackID(pAddr, m->getIsGlobal());

                this->udMems[target_udnodeid]->pushMessage(std::move(m), target_stid);
                break;
            }
            case basim::MType::M3Type:{
                // Send Message to another lane
                uint32_t target_udnodeid = m->getXe().getNWID().getNodeID();
                if (target_udnodeid != (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) {
                    #if defined(FASTSIM_NETWORK_TRACE)
                      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                      "<NODE2NODE, " +
                      std::to_string((udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) +" -> " +
                      std::to_string(target_udnodeid) +", " +
                      std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                      );
                      #endif

                      basim::LaneStats* loc_stats = uds[udid]->getLaneStats(laneID);
                      loc_stats->tran_count_other_node++;
                      loc_stats->tran_bytes_other_node += (m->getLen()+2) * WORDSIZE;
                    
                    uds[udid]->pushDelayedMessage(std::move(m));
                    break;
                }

                processMessageM3(std::move(m));
                break;
            }
            case basim::MType::M3Type_M:{
                basim::Addr destaddr = m->getdestaddr();
                common_addr DesAddr = mapPA2SA(destaddr,m->getIsGlobal());
                
                uint32_t target_udnodeid;
                uint32_t target_stid;

                target_udnodeid = m->getIsGlobal() ? DesAddr.node_id : udid / ((this->MachineConfig.NumStacks * this->MachineConfig.NumUDs));
                if (target_udnodeid != (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) {
                      #if defined(FASTSIM_NETWORK_TRACE)
                      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                      "<NODE2DRAM_ST, " +
                      std::to_string((udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) +" -> " +
                      std::to_string(target_udnodeid) +", " +
                      std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                      );
                      #endif

                      basim::LaneStats* loc_stats = uds[udid]->getLaneStats(laneID);
                      loc_stats->dram_store_count_other_node++;
                      loc_stats->dram_store_bytes_other_node += (m->getLen() + 2) * WORDSIZE;
                    
                    uds[udid]->pushDelayedMessage(std::move(m));
                    break;
                }
                target_stid = this->getMemoryMessageTargetStackID(destaddr, m->getIsGlobal());

                this->udMems[target_udnodeid]->pushMessage(std::move(m), target_stid);
                break;
            }
            case basim::MType::M4Type:{
                uint32_t target_udnodeid = m->getXe().getNWID().getNodeID();
                if (target_udnodeid != (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) {
                    #if defined(FASTSIM_NETWORK_TRACE)
                    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                    "<NODE2NODE, " +
                    std::to_string((udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) +" -> " +
                    std::to_string(target_udnodeid) +", " +
                    std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                    );
                    #endif
                    basim::LaneStats* loc_stats = uds[udid]->getLaneStats(laneID);
                    loc_stats->tran_count_other_node++;
                    loc_stats->tran_bytes_other_node += (m->getLen()+2) * WORDSIZE;
                    uds[udid]->pushDelayedMessage(std::move(m));
                    break;
                }

                processMessageM4(std::move(m));
                break;
            }
            case basim::MType::M4Type_M:{
                basim::Addr destaddr = m->getdestaddr();
                common_addr DesAddr = mapPA2SA(destaddr,m->getIsGlobal());

                uint32_t target_udnodeid;
                uint32_t target_stid;

                target_udnodeid = m->getIsGlobal() ? DesAddr.node_id : (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs));
                if (target_udnodeid != (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) {
                      #if defined(FASTSIM_NETWORK_TRACE)
                      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                      "<NODE2DRAM_ST, " +
                      std::to_string((udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs))) +" -> " +
                      std::to_string(target_udnodeid) +", " +
                      std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                      );
                      #endif
                      basim::LaneStats* loc_stats = uds[udid]->getLaneStats(laneID);
                      loc_stats->dram_store_count_other_node++;
                      loc_stats->dram_store_bytes_other_node += (m->getLen()+2) * WORDSIZE;
                        
                    uds[udid]->pushDelayedMessage(std::move(m));
                    break;
                }
                target_stid = this->getMemoryMessageTargetStackID(destaddr, m->getIsGlobal());

                this->udMems[target_udnodeid]->pushMessage(std::move(m), target_stid);
                break;
            }
            default:{
                BASIM_ERROR("Undefined Message type in Send Buffer");
                break;
            }
        }
    }
}

bool BASimUDRuntime_t::popDelayedMessageUD(uint32_t udid) {
  bool popped = false;
  while(true){
      uint32_t nodeid = udid / (this->MachineConfig.NumUDs * this->MachineConfig.NumStacks);
      if(network_output_limit > 0 && (this->simNodeStats[nodeid].output_bytes[0]->load() + 88) >= network_output_limit){  // set network bandwidth and output network traffic on node nodeid is full
        return true;
      }
      std::unique_ptr<basim::MMessage> m = uds[udid]->popDelayedMessage();
      if (!m) {
        return popped;
      }
      popped = true;
      switch(m->getType()){
          case basim::MType::M1Type:{
              uint32_t destNodeID = m->getXe().getNWID().getNodeID();
              uint32_t srcNodeID = udid / (this->MachineConfig.NumUDs * this->MachineConfig.NumStacks);

              #if defined(FASTSIM_NETWORK_TRACE)
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
              "<NODE2NODE, " +
              std::to_string(srcNodeID) +" -> " +
              std::to_string(destNodeID) +", " +
              std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
              );
              #endif

              // Node to node statistics
              this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add((m->getLen()+2) * WORDSIZE);

              #if defined(NETWORK_STATS)
              (this->simNodeStats[srcNodeID].tran_bytes_other_node[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].tran_count_other_node[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].total_bytes_other_node[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].total_count_other_node[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].max_tran_bytes_other_node_tmp[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].max_tran_count_other_node_tmp[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[destNodeID][(m->getLen()+2)])->fetch_add(1);
              (this->simNodeStats[srcNodeID].tran_packet_size_other_node_histogram[destNodeID][(m->getLen()+2)])->fetch_add(1);
              this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
              #endif
    
              processMessageM1(std::move(m));
              break;
          }
          case basim::MType::M2Type:{
              basim::Addr pAddr = m->getdestaddr();
              common_addr sAddr = mapPA2SA(pAddr, m->getIsGlobal());
              uint32_t target_udnodeid;
              uint32_t target_stid;

              target_udnodeid = m->getIsGlobal() ? sAddr.node_id : (udid / (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs));
              target_stid = this->getMemoryMessageTargetStackID(pAddr, m->getIsGlobal());


              uint32_t srcNodeID = udid / (this->MachineConfig.NumUDs * this->MachineConfig.NumStacks);
              if(m->isStore()){

                #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
                "<NODE2DRAM_ST, " +
                std::to_string(srcNodeID) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                );
                #endif

                // Node to node statistics
                this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add((m->getLen()+2) * WORDSIZE);

                #if defined(NETWORK_STATS)
                this->simNodeStats[srcNodeID].dram_store_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].dram_store_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_dram_store_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_dram_store_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].dram_store_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
                #endif

              }else{
                #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
                "<NODE2DRAM_LD, " +
                std::to_string(srcNodeID) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string(2 * WORDSIZE) + "B>"
                );
                #endif

                // Node to node statistics
                this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add(2 * WORDSIZE);
                
                #if defined(NETWORK_STATS)
                this->simNodeStats[srcNodeID].dram_load_bytes_other_node[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].dram_load_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_dram_load_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].max_dram_load_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].dram_load_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
                this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
                #endif

              }

              this->udMems[target_udnodeid]->pushMessage(std::move(m), target_stid);
              break;
              
          }
          case basim::MType::M3Type:{
              uint32_t srcNodeID = udid / (this->MachineConfig.NumUDs * this->MachineConfig.NumStacks);
              uint32_t destNodeID = m->getXe().getNWID().getNodeID();

              #if defined(FASTSIM_NETWORK_TRACE)
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
              "<NODE2NODE, " +
              std::to_string(srcNodeID) +" -> " +
              std::to_string(destNodeID) +", " +
              std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
              );
              #endif
              

              // Node to node statistics
              this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add((m->getLen()+2) * WORDSIZE);

              #if defined(NETWORK_STATS)
              this->simNodeStats[srcNodeID].tran_bytes_other_node[destNodeID]->fetch_add((m->getLen()+2) * WORDSIZE);
              this->simNodeStats[srcNodeID].tran_count_other_node[destNodeID]->fetch_add(1);
              this->simNodeStats[srcNodeID].total_bytes_other_node[destNodeID]->fetch_add((m->getLen()+2) * WORDSIZE);
              this->simNodeStats[srcNodeID].total_count_other_node[destNodeID]->fetch_add(1);
              (this->simNodeStats[srcNodeID].max_tran_bytes_other_node_tmp[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].max_tran_count_other_node_tmp[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[destNodeID][(m->getLen()+2)])->fetch_add(1);
              (this->simNodeStats[srcNodeID].tran_packet_size_other_node_histogram[destNodeID][(m->getLen()+2)])->fetch_add(1);
              this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
              #endif

              processMessageM3(std::move(m));
              break;
          }
          case basim::MType::M3Type_M:{
              basim::Addr destaddr = m->getdestaddr();
              common_addr DesAddr = mapPA2SA(destaddr,m->getIsGlobal());
              uint32_t target_udnodeid;
              uint32_t target_stid;

              target_udnodeid = m->getIsGlobal() ? DesAddr.node_id : udid / ((this->MachineConfig.NumStacks * this->MachineConfig.NumUDs));
              target_stid = this->getMemoryMessageTargetStackID(destaddr, m->getIsGlobal());


              uint32_t srcNodeID = udid / (this->MachineConfig.NumUDs * this->MachineConfig.NumStacks);

                #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
                "<NODE2DRAM_ST, " +
                std::to_string(srcNodeID) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                );
                #endif


              // Node to node statistics
              this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add((m->getLen()+2) * WORDSIZE);

                #if defined(NETWORK_STATS)
                this->simNodeStats[srcNodeID].dram_store_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].dram_store_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_dram_store_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_dram_store_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].dram_store_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
                #endif

              this->udMems[target_udnodeid]->pushMessage(std::move(m), target_stid);
              break;
          }
          case basim::MType::M4Type:{
              uint32_t srcNodeID = udid / (this->MachineConfig.NumUDs * this->MachineConfig.NumStacks);
              uint32_t destNodeID = m->getXe().getNWID().getNodeID();

              #if defined(FASTSIM_NETWORK_TRACE)
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
              "<NODE2NODE, " +
              std::to_string(srcNodeID) +" -> " +
              std::to_string(destNodeID) +", " +
              std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
              );
              #endif

              // Node to node statistics
              this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add((m->getLen()+2) * WORDSIZE);

              #if defined(NETWORK_STATS)
              (this->simNodeStats[srcNodeID].tran_bytes_other_node[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].tran_count_other_node[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].total_bytes_other_node[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].total_count_other_node[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].max_tran_bytes_other_node_tmp[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].max_tran_count_other_node_tmp[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[destNodeID])->fetch_add((m->getLen()+2) * WORDSIZE);
              (this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[destNodeID])->fetch_add(1);
              (this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[destNodeID][(m->getLen()+2)])->fetch_add(1);
              (this->simNodeStats[srcNodeID].tran_packet_size_other_node_histogram[destNodeID][(m->getLen()+2)])->fetch_add(1);
              this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
              #endif

              processMessageM4(std::move(m));
              break;
          }
          case basim::MType::M4Type_M:{
              basim::Addr destaddr = m->getdestaddr();
              common_addr DesAddr = mapPA2SA(destaddr,m->getIsGlobal());
              uint32_t target_udnodeid;
              uint32_t target_stid;

              target_udnodeid = m->getIsGlobal() ? DesAddr.node_id : udid / ((this->MachineConfig.NumStacks * this->MachineConfig.NumUDs));
              target_stid = this->getMemoryMessageTargetStackID(destaddr, m->getIsGlobal());

              uint32_t srcNodeID = udid / (this->MachineConfig.NumUDs * this->MachineConfig.NumStacks);

              #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
                "<NODE2DRAM_ST, " +
                std::to_string(srcNodeID) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                );
                #endif


              // Node to node statistics
              this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add((m->getLen()+2) * WORDSIZE);

                #if defined(NETWORK_STATS)
                this->simNodeStats[srcNodeID].dram_store_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].dram_store_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_dram_store_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_dram_store_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].dram_store_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
                #endif

              this->udMems[target_udnodeid]->pushMessage(std::move(m), target_stid);
              break;
          }
          default:{
              BASIM_ERROR("Undefined Message type in Delayed Buffer UD");
              break;
          }
      }
      //uds[udid]->removeSendMessage(i);
  }
}
    
bool BASimUDRuntime_t::popMemory(uint32_t udnodeid, uint32_t stackID) {
  bool popped = false;
  while (true) {
    std::unique_ptr<basim::MMessage> m = this->udMems[udnodeid]->popMessage(stackID);
    if (!m) {
      break;
    }
    popped = true;

    switch(m->getType()){
      case basim::MType::M2Type:{
          uint32_t target_udnodeid = m->getXc().getNWID().getNodeID();
          if (target_udnodeid != udnodeid) {
            if(m->isStore()){
                #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                "<DRAM2NODE_ST_ACK, " +
                std::to_string(udnodeid) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string(2* WORDSIZE) + "B>"
                );
                #endif

                
            } else{
                #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                "<DRAM2NOD_LD_ACK, " +
                std::to_string(udnodeid) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                );
                #endif

            }
            this->udMems[udnodeid]->pushDelayedMessage(std::move(m), stackID);
            break;
          }
          
          processMessageM2(std::move(m), udnodeid);
          break;
      }
      case basim::MType::M3Type_M:{
          uint32_t target_udnodeid = m->getXc().getNWID().getNodeID();
          if (target_udnodeid != udnodeid) {
             #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                "<DRAM2NODE_ST_ACK, " +
                std::to_string(udnodeid) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string(2* WORDSIZE) + "B>"
                );
                #endif

            this->udMems[udnodeid]->pushDelayedMessage(std::move(m), stackID);
            break;
          }
          processMessageM3M(std::move(m));
          break;
      }
      case basim::MType::M4Type_M:{
          uint32_t target_udnodeid = m->getXc().getNWID().getNodeID();
          if (target_udnodeid != udnodeid) {
            #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_SEND_MSG",
                "<DRAM2NODE_ST_ACK, " +
                std::to_string(udnodeid) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string(2* WORDSIZE) + "B>"
                );
                #endif

            this->udMems[udnodeid]->pushDelayedMessage(std::move(m), stackID);
            break;
          }  
          processMessageM4M(std::move(m));
          break;
      }
      default:{
          BASIM_ERROR("Undefined Message type in MEM Buffer");
          break;
      }
    }
  }
  return popped;
}

bool BASimUDRuntime_t::popDelayedMessageMEM(uint32_t udnodeid, uint32_t stackID) {
  bool popped = false;
  uint32_t srcNodeID = udnodeid;
  while (true) {
      if(network_output_limit > 0 && (this->simNodeStats[srcNodeID].output_bytes[0]->load() + 88) >= network_output_limit){  // set network bandwidth and output network traffic on node nodeid is full
        return true;
      }
    std::unique_ptr<basim::MMessage> m = this->udMems[udnodeid]->popDelayedMessage(stackID);
    if (!m) {
      break;
    }
    popped = true;

    switch(m->getType()){
      case basim::MType::M2Type:{
          uint32_t target_udnodeid = m->getXc().getNWID().getNodeID();
          if(m->isStore()){

                #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
                "<DRAM2NODE_ST_ACK, " +
                std::to_string(udnodeid) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string(2* WORDSIZE) + "B>"
                );
                #endif

                basim::LaneStats* loc_stats = uds[m->getXc().getNWID().getUDID()]->getLaneStats(m->getXc().getNWID().getLaneID());
                loc_stats->dram_store_ack_count_other_node++;
                loc_stats->dram_store_ack_bytes_other_node += 2 * WORDSIZE;

                this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add(2 * WORDSIZE);

                #if defined(NETWORK_STATS)
                this->simNodeStats[srcNodeID].dram_store_ack_bytes_other_node[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].dram_store_ack_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_dram_store_ack_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].max_dram_store_ack_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
                this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].dram_store_ack_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
                this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
                #endif
                
            } else{
                #if defined(FASTSIM_NETWORK_TRACE)
                basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
                "<DRAM2NOD_LD_ACK, " +
                std::to_string(udnodeid) +" -> " +
                std::to_string(target_udnodeid) +", " +
                std::to_string((m->getLen()+2) * WORDSIZE) + "B>"
                );
                #endif

                basim::LaneStats* loc_stats = uds[m->getXc().getNWID().getUDID()]->getLaneStats(m->getXc().getNWID().getLaneID());
                loc_stats->dram_load_ack_count_other_node++;
                loc_stats->dram_load_ack_bytes_other_node += (m->getLen()+2) * WORDSIZE;

                this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add((m->getLen()+2) * WORDSIZE);

                #if defined(NETWORK_STATS)
                this->simNodeStats[srcNodeID].dram_load_ack_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].dram_load_ack_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_dram_load_ack_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_dram_load_ack_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add((m->getLen()+2) * WORDSIZE);
                this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
                this->simNodeStats[srcNodeID].dram_load_ack_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][(m->getLen()+2)]->fetch_add(1);
                this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
                #endif

            }

          processMessageM2(std::move(m), udnodeid);
          break;
      }
      case basim::MType::M3Type_M:{
          uint32_t target_udnodeid = m->getXc().getNWID().getNodeID();
          #if defined(FASTSIM_NETWORK_TRACE)
          basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
          "<DRAM2NODE_ST_ACK, " +
          std::to_string(udnodeid) +" -> " +
          std::to_string(target_udnodeid) +", " +
          std::to_string(2* WORDSIZE) + "B>"
          );
          #endif

          basim::LaneStats* loc_stats = uds[m->getXc().getNWID().getUDID()]->getLaneStats(m->getXc().getNWID().getLaneID());
          loc_stats->dram_store_ack_count_other_node++;
          loc_stats->dram_store_ack_bytes_other_node += 2 * WORDSIZE;

          this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add(2 * WORDSIZE);

          #if defined(NETWORK_STATS)
          this->simNodeStats[srcNodeID].dram_store_ack_bytes_other_node[target_udnodeid]->fetch_add((2) * WORDSIZE);
          this->simNodeStats[srcNodeID].dram_store_ack_count_other_node[target_udnodeid]->fetch_add(1);
          this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add(2 * WORDSIZE);
          this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
          this->simNodeStats[srcNodeID].max_dram_store_ack_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
          this->simNodeStats[srcNodeID].max_dram_store_ack_count_other_node_tmp[target_udnodeid]->fetch_add(1);
          this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
          this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
          this->simNodeStats[srcNodeID].dram_store_ack_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
          this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
          this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
          #endif

          processMessageM3M(std::move(m));
          break;
      }
      case basim::MType::M4Type_M:{        
          uint32_t target_udnodeid = m->getXc().getNWID().getNodeID();
          
          #if defined(FASTSIM_NETWORK_TRACE)
          basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "NETWORK_RECEIVE_MSG",
          "<DRAM2NODE_ST_ACK, " +
          std::to_string(udnodeid) +" -> " +
          std::to_string(target_udnodeid) +", " +
          std::to_string(2* WORDSIZE) + "B>"
          );
          #endif
          
            basim::LaneStats* loc_stats = uds[m->getXc().getNWID().getUDID()]->getLaneStats(m->getXc().getNWID().getLaneID());
            loc_stats->dram_store_ack_count_other_node++;
            loc_stats->dram_store_ack_bytes_other_node += 2 * WORDSIZE;

            this->simNodeStats[srcNodeID].output_bytes[0]->fetch_add(2 * WORDSIZE);

            #if defined(NETWORK_STATS)
            this->simNodeStats[srcNodeID].dram_store_ack_bytes_other_node[target_udnodeid]->fetch_add(2 * WORDSIZE);
            this->simNodeStats[srcNodeID].dram_store_ack_count_other_node[target_udnodeid]->fetch_add(1);
            this->simNodeStats[srcNodeID].total_bytes_other_node[target_udnodeid]->fetch_add(2 * WORDSIZE);
            this->simNodeStats[srcNodeID].total_count_other_node[target_udnodeid]->fetch_add(1);
            this->simNodeStats[srcNodeID].max_dram_store_ack_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
            this->simNodeStats[srcNodeID].max_dram_store_ack_count_other_node_tmp[target_udnodeid]->fetch_add(1);
            this->simNodeStats[srcNodeID].max_total_bytes_other_node_tmp[target_udnodeid]->fetch_add(2 * WORDSIZE);
            this->simNodeStats[srcNodeID].max_total_count_other_node_tmp[target_udnodeid]->fetch_add(1);
            this->simNodeStats[srcNodeID].dram_store_ack_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
            this->simNodeStats[srcNodeID].total_packet_size_other_node_histogram[target_udnodeid][2]->fetch_add(1);
            this->simNodeStats[srcNodeID].output_counts[0]->fetch_add(1);
            #endif

          processMessageM4M(std::move(m));
          break;
      }
      default:{
          BASIM_ERROR("Undefined Message type in Delayed Buffer MEM");
          break;
      }
    }
  }
  return popped;
}

void BASimUDRuntime_t::processMessageM1(std::unique_ptr<basim::MMessage> m) {
    basim::eventword_t ev = m->getXe();
    // Send Message to another lane
    basim::operands_t op0(m->getLen(), m->getXc());  // num operands + cont
    //op0.setData((m->getpayload()).get());
    op0.setData((m->getpayload()));
    basim::eventoperands_t eops(&ev, &op0);
    int ud = getUDIdx(ev.getNWID());
    #ifndef SENDPOLICY
      sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
    #else
      int policy = (ev.getNWID()).getSendPolicy();
      if(policy == 7) {
        basim::Addr addr = m->getdestaddr();
        ud = getUDIdxForAddr(ev.getNWID(), addr, m->getIsGlobal());
        int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), (ev.getNWID()).getSendPolicy());
        sendEventOperands(ud, &eops, laneid);
      }else{
        int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), policy);
        sendEventOperands(ud, &eops, laneid);
      }
    #endif
      #if defined(FASTSIM_TRACE_MSG)
      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
        "<LANE2LANE, " +
        std::to_string(m->getSrcEventWord().getNWID().getUDName()) + ":" +
        std::to_string(m->getSrcEventWord().getThreadID()) +" -> " +
        std::to_string(m->getXe().getNWID().getUDName()) + ":" +
        std::to_string(m->getXe().getThreadID()) +", " +
        std::to_string(m->getMsgSize()) + ">"
        );
      #endif
}

void BASimUDRuntime_t::processMessageM2(std::unique_ptr<basim::MMessage> m, uint32_t udnodeid) {
    basim::Addr pAddr = m->getdestaddr();
    common_addr sAddr = mapPA2SA(pAddr, m->getIsGlobal());
    // Send to Memory
    basim::eventword_t* cont = new basim::EventWord();
    *cont = m->getXc();
    if(m->isStore()){
      // Writes to memory
      word_t* dataptr = (m->getpayload()); // get the data and store it in memory
      word_t* dst = reinterpret_cast<word_t*>(sAddr.addr);
      std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
      // Post store event push
      uint64_t noupdate_cont = 0x7fffffffffffffff;
      basim::operands_t op0(2, basim::EventWord(noupdate_cont));  // num operands + cont
      int ud = getUDIdx(cont->getNWID());
      uint64_t dest_va = getVirtualAddr(ud, m->getdestaddr(), m->getIsGlobal());
      op0.setDataWord(0, dest_va);
      op0.setDataWord(1, dest_va);
      basim::eventoperands_t eops(cont, &op0);
      sendEventOperands(ud, &eops, (cont->getNWID()).getLaneID());
      #if defined(FASTSIM_TRACE_MSG)
      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
        "<LANE2MEM_ST, " +
        std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
        basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + ", " +
        std::to_string(m->getMsgSize()) + ">"
        );
      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
        "<MEM2LANE_ST, " +
        basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + " -> " +
        std::to_string(m->getXc().getNWID().getUDName()) + ", " +
        std::to_string((2 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
        );
      #endif
    }else{
      // Reads from memory
      word_t* dataptr = reinterpret_cast<word_t*>(sAddr.addr);
      m->addpayload(dataptr);
      word_t* dst = (m->getpayload());
      uint64_t noupdate_cont = 0x7fffffffffffffff;
      basim::operands_t op0(m->getLen() + 1, basim::EventWord(noupdate_cont));  // num operands + dram addr (cont added by constructor)
      for (int im = 0; im < m->getLen(); im++) {
        op0.setDataWord(im, dst[im]);
      }
      uint64_t dest_va = getVirtualAddr(udnodeid, m->getdestaddr(), m->getIsGlobal());
      op0.setDataWord(m->getLen(), dest_va);
      basim::eventoperands_t eops(cont, &op0);
      int ud = getUDIdx(cont->getNWID());
      sendEventOperands(ud, &eops, (cont->getNWID()).getLaneID());
      // delete[] dst;
      #if defined(FASTSIM_TRACE_MSG)
      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
        "<LANE2MEM_LD, " +
        std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
        basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + ", " +
        std::to_string(m->getMsgSize()) + ">"
        );
      basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
        "<MEM2LANE_LD, " +
        basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + " -> " +
        std::to_string(m->getXc().getNWID().getUDName()) + ", " +
        std::to_string((m->getLen() + 1 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
        );
      #endif
    }
    delete cont;
}

void BASimUDRuntime_t::processMessageM3(std::unique_ptr<basim::MMessage> m) {
    // Send Message to another lane
    basim::eventword_t ev = m->getXe();
    basim::operands_t op0(m->getLen(), m->getXc());  // num operands + cont
    op0.setData((m->getpayload()));
    basim::eventoperands_t eops(&ev, &op0);
    int ud = getUDIdx(ev.getNWID());
    #ifndef SENDPOLICY
      sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
    #else
      int policy = (ev.getNWID()).getSendPolicy();
      if(policy == 7){
        basim::Addr addr = m->getdestaddr();
        ud = getUDIdxForAddr(ev.getNWID(), addr, m->getIsGlobal());
        int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), (ev.getNWID()).getSendPolicy());
        sendEventOperands(ud, &eops, laneid);
      }else{
        int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), (ev.getNWID()).getSendPolicy());
        sendEventOperands(ud, &eops, laneid);
      }
    #endif
    #if defined(FASTSIM_TRACE_MSG)
    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
      "<LANE2LANE, " +
      std::to_string(m->getSrcEventWord().getNWID().getUDName()) + ":" +
      std::to_string(m->getSrcEventWord().getThreadID()) +" -> " +
      std::to_string(m->getXe().getNWID().getUDName()) + ":" +
      std::to_string(m->getXe().getThreadID()) +", " +
      std::to_string(m->getMsgSize()) + ">"
      );
    #endif
}

void BASimUDRuntime_t::processMessageM3M(std::unique_ptr<basim::MMessage> m) {
    basim::Addr destaddr = m->getdestaddr();
    common_addr DesAddr = mapPA2SA(destaddr,m->getIsGlobal());
    // Always a store (2 words)
    basim::eventword_t cont = m->getXc();
    // Writes to memory
    word_t* dataptr = (m->getpayload()); // get the data and store it in memory
    word_t* dst = reinterpret_cast<word_t*>(DesAddr.addr);
    std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
    // Post store event push
    uint64_t noupdate_cont = 0x7fffffffffffffff;
    basim::operands_t op0(2, basim::EventWord(noupdate_cont));  // num opernads + cont
    int ud = getUDIdx(cont.getNWID());
    uint64_t dest_va = getVirtualAddr(ud, m->getdestaddr(), m->getIsGlobal());
    op0.setDataWord(0, dest_va);
    op0.setDataWord(1, dest_va);
    basim::eventoperands_t eops(&cont, &op0);
    sendEventOperands(ud, &eops, (cont.getNWID()).getLaneID());
    #if defined(FASTSIM_TRACE_MSG)
    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
      "<LANE2MEM_ST, " +
      std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
      basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + ", " +
      std::to_string(m->getMsgSize()) + ">"
      );
    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
      "<MEM2LANE_ST, " +
      basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + " -> " +
      std::to_string(m->getXc().getNWID().getUDName()) + ", " +
      std::to_string((2 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
      );
    #endif
}

void BASimUDRuntime_t::processMessageM4(std::unique_ptr<basim::MMessage> m) {
    // Send Message to another lane
    // Merge this with M3Type
    basim::eventword_t ev = m->getXe();
    basim::operands_t op0(m->getLen(), m->getXc());  // num operands + cont
    op0.setData((m->getpayload()));
    basim::eventoperands_t eops(&ev, &op0);
    int ud = getUDIdx(ev.getNWID());
    #ifndef SENDPOLICY
        sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
    #else
      int policy = (ev.getNWID()).getSendPolicy();
      if(policy == 7){
        basim::Addr addr = m->getdestaddr();
        ud = getUDIdxForAddr(ev.getNWID(), addr, m->getIsGlobal());
        int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), (ev.getNWID()).getSendPolicy());
        sendEventOperands(ud, &eops, laneid);
      }else{
        int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), (ev.getNWID()).getSendPolicy());
        sendEventOperands(ud, &eops, laneid);
      }
    #endif
    #if defined(FASTSIM_TRACE_MSG)
    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
      "<LANE2LANE, " +
      std::to_string(m->getSrcEventWord().getNWID().getUDName()) + ":" +
      std::to_string(m->getSrcEventWord().getThreadID()) +" -> " +
      std::to_string(m->getXe().getNWID().getUDName()) + ":" +
      std::to_string(m->getXe().getThreadID()) +", " +
      std::to_string(m->getMsgSize()) + ">"
      );
    #endif
}

void BASimUDRuntime_t::processMessageM4M(std::unique_ptr<basim::MMessage> m) {
    basim::Addr destaddr = m->getdestaddr();
    common_addr DesAddr = mapPA2SA(destaddr,m->getIsGlobal());
    // Always a store (2 words)
    // Merge this with M3Type_M
    basim::eventword_t cont = m->getXc();
    // Writes to memory
    word_t* dataptr = (m->getpayload()); // get the data and store it in memory
    word_t* dst = reinterpret_cast<word_t*>(DesAddr.addr);
    std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
    // Post store event push
    uint64_t noupdate_cont = 0x7fffffffffffffff;
    basim::operands_t op0(2, basim::EventWord(noupdate_cont));  // num opernads + cont
    int ud = getUDIdx(cont.getNWID());
    uint64_t dest_va = getVirtualAddr(ud, m->getdestaddr(), m->getIsGlobal());
    op0.setDataWord(0, dest_va);
    op0.setDataWord(1, dest_va);
    basim::eventoperands_t eops(&cont, &op0);
    sendEventOperands(ud, &eops, (cont.getNWID()).getLaneID());
    #if defined(FASTSIM_TRACE_MSG)
    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
      "<LANE2MEM_ST, " +
      std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
      basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + ", " +
      std::to_string(m->getMsgSize()) + ">"
      );
    basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
      "<MEM2LANE_ST, " +
      basim::addr2HexString(reinterpret_cast<void *>(dest_va)) + " -> " +
      std::to_string(m->getXc().getNWID().getUDName()) + ", " +
      std::to_string((2 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
      );
    #endif
}

void BASimUDRuntime_t::sendEventOperands(int sourceUDID, basim::eventoperands_t *eops, uint32_t targetLaneID) {
    uds[sourceUDID]->pushEventOperands(*eops, targetLaneID);
}

uint64_t BASimUDRuntime_t::getVirtualAddr(int sourceUDID, uint64_t addr, bool isGlobal) {
    return uds[sourceUDID]->translate_pa2va(addr, isGlobal);
}

#ifdef ASST_FASTSIM
    void BASimUDRuntime_t::start_exec(networkid_t nwid) {
        if(nwid.get_NodeId() == nodeID && send_event_valid){
            send_event2(send_event_ev);
        }
    }
#else
    void BASimUDRuntime_t::start_exec(networkid_t nwid) {
        UDRuntime_t::start_exec(nwid);

        // Then we do a round-robin execution of all the lanes while
        // there is something executing
        if(pthread_mutex_trylock(&mutex) == 0) {
            bool something_exec;
            uint64_t num_iterations = 0;
            do {
                something_exec = false;
                #ifndef GEM5_MODE
                
                /*------------------------ network initialization -------------------------*/
                // reset node tmp stats for max network bandwidth
                for(uint32_t nodeID = 0; nodeID < this->MachineConfig.NumNodes; nodeID++){
                  this->simNodeStats[nodeID].reset_tmp(this->MachineConfig.NumNodes);
                }
                network_output_limit = NumTicks * this->MachineConfig.InterNodeBandwidth / 2; // 2 is because of 2GHz
                // printf("network_output_limit = %lu\n", network_output_limit);
                // fflush(stdout);
                /*------------------------ network initialization end-------------------------*/
                
                    for (uint32_t ud = 0; ud < total_uds; ud++) {
                        uds[ud]->tock(NumTicks);
                    }
                    for (uint32_t node = 0; node < this->MachineConfig.NumNodes; node++) {
                        this->udMems[node]->tick(NumTicks);
                    }
                    
                    #pragma omp parallel for schedule(runtime) reduction(|| : something_exec) // ud level parallelism
                    for (uint32_t ud = 0; ud < total_uds; ud++) {
                        for (uint32_t ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
                            if (!uds[ud]->isIdle(ln)) {
                                something_exec = true;
                                uds[ud]->simulate(ln, NumTicks, globalTick);
                            }
                        }
                    }
                    // OMP: implicit barrier
                      
                    bool something_popped = false;
                    #pragma omp parallel for schedule(runtime) reduction(|| : something_popped)
                    for (uint32_t ud = 0; ud < total_uds; ud++) {
                        if(something_exec) {
                            for (uint32_t ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
                                postSimulate(ud, ln);
                            }
                        }
                        something_popped |= popDelayedMessageUD(ud);
                    }
                    // OMP: implicit barrier

                    something_exec |= something_popped;

                    // Memory operations
                    #pragma omp parallel for collapse(2) schedule(runtime) reduction(|| : something_exec)
                    for (uint32_t st = 0; st < this->MachineConfig.NumStacks; st++) {
                        for (uint32_t node = 0; node < this->MachineConfig.NumNodes; node++) {
                            something_exec |= popMemory(node, st) | popDelayedMessageMEM(node, st);
                        }
                    }
                    // OMP: implicit barrier

                    for (uint32_t node = 0; node < this->MachineConfig.NumNodes; node++) {
                        for (uint32_t st = 0; st < this->MachineConfig.NumStacks; st++) {
                            this->udMems[node]->updateStats(st);
                        }
                    }
                    
                    num_start_exe++;
                    // printf(" num_start_exe = %lu\n",  num_start_exe);
                    // fflush(stdout);
                    #if defined(NETWORK_STATS)
                    for (uint32_t node = 0; node < this->MachineConfig.NumNodes; node++) {
                      for (uint32_t dstNodeID = 0; dstNodeID < this->MachineConfig.NumNodes; dstNodeID++) {
                        uint64_t node_stats_tmp = std::max(this->simNodeStats[node].max_total_count_other_node[dstNodeID]->load(), this->simNodeStats[node].max_total_count_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_total_count_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_total_bytes_other_node[dstNodeID]->load(), this->simNodeStats[node].max_total_bytes_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_total_bytes_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_tran_count_other_node[dstNodeID]->load(), this->simNodeStats[node].max_tran_count_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_tran_count_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_tran_bytes_other_node[dstNodeID]->load(), this->simNodeStats[node].max_tran_bytes_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_tran_bytes_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_store_count_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_store_count_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_store_count_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_load_count_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_load_count_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_load_count_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_store_bytes_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_store_bytes_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_store_bytes_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_load_bytes_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_load_bytes_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_load_bytes_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_store_ack_count_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_store_ack_count_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_store_ack_count_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_load_ack_count_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_load_ack_count_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_load_ack_count_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_store_ack_bytes_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_store_ack_bytes_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_store_ack_bytes_other_node[dstNodeID]->store(node_stats_tmp);
                        node_stats_tmp = std::max(this->simNodeStats[node].max_dram_load_ack_bytes_other_node[dstNodeID]->load(), this->simNodeStats[node].max_dram_load_ack_bytes_other_node_tmp[dstNodeID]->load());
                        this->simNodeStats[node].max_dram_load_ack_bytes_other_node[dstNodeID]->store(node_stats_tmp);

                      }
                      // printf(" finish pairwise network stats %d \n", node);
                      // fflush(stdout);
                      uint64_t node_stats_tmp = std::max(this->simNodeStats[node].max_bytes[0]->load(), this->simNodeStats[node].output_bytes[0]->load());
                      this->simNodeStats[node].max_bytes[0]->store(node_stats_tmp);
                      node_stats_tmp = std::max(this->simNodeStats[node].max_counts[0]->load(), this->simNodeStats[node].output_counts[0]->load());
                      this->simNodeStats[node].max_counts[0]->store(node_stats_tmp);
                      uint64_t len = 0;
                      for(uint32_t j = 0; j < MachineConfig.NumUDs * MachineConfig.NumStacks; j++){
                        uint64_t udid = node * MachineConfig.NumUDs * MachineConfig.NumStacks + j;
                        len = len + uds[udid]->DelayedMessageLen();
                      }
                      this->simNodeStats[node].total_queue_size[0]->fetch_add(len);
                      node_stats_tmp = std::max(this->simNodeStats[node].max_queue_size[0]->load(), len);
                      this->simNodeStats[node].max_queue_size[0]->store(node_stats_tmp);
                      // printf(" finish cross-node network stats %d\n", node);
                      // fflush(stdout);

                    }
                    #endif

                    // printf(" finish \n");
                    //   fflush(stdout);


                #else
                    for (uint32_t ud = 0; ud < total_uds; ud++) {
                        for (uint32_t ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
                            if (!uds[ud]->isIdle(ln)) {
                                something_exec = true;
                                uds[ud]->simulate(ln, NumTicks, globalTick);
                                postSimulateGem5(ud, ln);
                            }
                        }
                    }
                #endif
            globalTick += NumTicks;
            simTicks += NumTicks;
            } while (something_exec &&
                   (!max_sim_iterations || ++num_iterations < max_sim_iterations));
            pthread_mutex_unlock(&mutex);
        }
    }
#endif



void BASimUDRuntime_t::t2ud_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset) {
#ifdef ASST_FASTSIM
  assert(nwid.get_NodeId() == nodeID && "Error, nwid is not current UpDown node");
  nwid.nodeid = 0;
#endif
        
  UDRuntime_t::t2ud_memcpy(data, size, nwid, offset);
  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset); 
                  // UDRuntime_t::get_ud_physical_memory(nwid);
  uint8_t* data_ptr = reinterpret_cast<uint8_t *>(data);
  for (int i = 0; i < size / sizeof(word_t); i++) {
    // Address is local
    uds[ud_num]->writeScratchPad(sizeof(word_t), addr, reinterpret_cast<uint8_t *>(data_ptr));
    addr += sizeof(word_t);
    data_ptr += sizeof(word_t);
  }
}

void BASimUDRuntime_t::ud2t_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset) {

#ifdef ASST_FASTSIM
  assert(nwid.get_NodeId() == nodeID && "Error, nwid is not current UpDown node");
  nwid.nodeid = 0;
#endif

  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset);
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
  //if (python_enabled)
  //  upstream_pyintf[ud_num]->read_scratch(
  //      addr, reinterpret_cast<uint8_t *>(base), size);
  uds[ud_num]->readScratchPad(sizeof(word_t), addr, reinterpret_cast<uint8_t*>(base));
  UDRuntime_t::ud2t_memcpy(data, size, nwid, offset);
}

bool BASimUDRuntime_t::test_addr(networkid_t nwid, uint32_t offset,
                               word_t expected) {
  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset);
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
  start_exec(nwid);
  uds[ud_num]->readScratchPad(sizeof(word_t), addr, reinterpret_cast<uint8_t*>(base));
  return UDRuntime_t::test_addr(nwid, offset, expected);
}

bool BASimUDRuntime_t::test_addr_without_exec(networkid_t nwid, uint32_t offset,
                               word_t expected) {

  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset);
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
  uds[ud_num]->readScratchPad(sizeof(word_t), addr, reinterpret_cast<uint8_t*>(base));
  bool end = UDRuntime_t::test_addr(nwid, offset, expected);
  return end;
}

void BASimUDRuntime_t::test_wait_addr(networkid_t nwid, uint32_t offset,
                                    word_t expected) {
#ifdef ASST_FASTSIM
    pthread_mutex_lock(&map_lock);
    pthread_t tid = pthread_self();
    int id1 = 0;
    auto it1 = thread_map.find(tid);
    if (it1 != thread_map.end()) {
        id1 = it1->second;
    }else{
        id1 = thread_num.load(std::memory_order_relaxed);
        thread_num.store(id1+1, std::memory_order_release);
        thread_map[tid] = id1;
    }
    pthread_mutex_unlock(&map_lock);


    assert(nwid.get_NodeId() == nodeID && "Error, nwid is not current UpDown node");
    networkid_t nwid2(nwid.get_LaneId(), nwid.get_UdId(), nwid.get_StackId(), 0);
    while(test_addr_flag[id1] != 0)
        fflush(stdout);
    test_nwid[id1] = nwid2;
    test_offset[id1] = offset;
    test_expected[id1] = expected;
    test_addr_flag[id1] = 1;
    sem_wait(&(semTest[id1]));
    // The bottom call will never hold since we're holding here
    UDRuntime_t::test_wait_addr(nwid2, offset, expected);
#else
    while (!test_addr(nwid, offset, expected));
    // The bottom call will never hold since we're holding here
    UDRuntime_t::test_wait_addr(nwid, offset, expected);
#endif
}


size_t BASimUDRuntime_t::dumpMemoryTranslation(std::string filename, uint64_t nodeID) {
    size_t storedBytes;
    filename += std::to_string(nodeID) + ".dram.dat";
    FILE* mem_file = fopen(filename.c_str(), "wb");
    UPDOWN_ERROR_IF(!mem_file, "DRAM Dump: NodeID %ld: Could not open %s", nodeID, filename.c_str());

    fseek(mem_file, 0, SEEK_SET);
    // Write 'F' to indicate dump by Fastsim
    storedBytes = fwrite("F", sizeof(char), 1, mem_file);
    // Write 'D' to indicate DRAM dump
    storedBytes += fwrite("D", sizeof(char), 1, mem_file);

    // include a version number for format changes (it also makes the file easier to read in hex editors, since the values are aligned now)
    uint16_t version = 1;
    storedBytes += fwrite(&version, sizeof(uint16_t), 1, mem_file);
    BASIM_INFOMSG("DRAM Dump: NodeID %ld: file version: %d", nodeID, version);

    // Get access to the translation memory. We should always have at least 1 UD.
    basim::TranslationMemoryPtr transmem = uds[0]->getTranslationMem();
    transmem->dumpSegments();

    // number of private segments in the dump file
    // TODO we do not dump them for the time being
    size_t nPrivateSegments = transmem->private_segments.size();
    storedBytes += fwrite(&nPrivateSegments, sizeof(size_t), 1, mem_file);
    BASIM_INFOMSG("DRAM Dump: NodeID %ld: number of private segments: %ld", nodeID, nPrivateSegments);

    // number of global segments in the dump file
    size_t nGlobalSegments = transmem->global_segments.size();
    storedBytes += fwrite(&nGlobalSegments, sizeof(size_t), 1, mem_file);
    BASIM_INFOMSG("DRAM Dump: NodeID %ld: number of global segments: %ld", nodeID, nGlobalSegments);

    // basim::Addr pAddr;
    // for(uint64_t i=0; i<size/8; i+=0x1'0000) {
    //   pAddr = transmem->translate_va2pa((basim::Addr)((uint64_t)vaddr + i*8), 1);
    //   printf("vAddr: %p, pAddr: %p\n", (uint64_t)vaddr + i*8, (uint64_t)pAddr);
    // }

    for (auto seg : transmem->global_segments) {

        BASIM_INFOMSG("DRAM Dump: NodeID %ld: Current segment:", nodeID);
        seg.print_info();

        // position of the metadata of the current segment in the file
        uint64_t metaPos = ftell(mem_file);
        BASIM_INFOMSG("DRAM Dump: NodeID %ld: Metadata position: %ld (0x%lx)\n", nodeID, metaPos, metaPos);
        BASIM_INFOMSG("DRAM Dump: NodeID %ld: Stored metadata: vBase: 0x%lx, vLimit: 0x%lx, swizzleMask: 0x%lx, pAddr: 0x%lx, blockSize: %ld, accessFlags: %d\n", nodeID, seg.virtual_base, seg.virtual_limit, seg.swizzle_mask.getMask(), seg.physical_base.getCompressed(), seg.block_size, seg.access_flags);

        // store the meta data
        storedBytes += fwrite(&(seg.virtual_base), sizeof(uint64_t), 1, mem_file);
        storedBytes += fwrite(&(seg.virtual_limit), sizeof(uint64_t), 1, mem_file);
        uint64_t tempValue = seg.swizzle_mask.getMask();
        storedBytes += fwrite(&tempValue, sizeof(uint64_t), 1, mem_file);
        storedBytes += fwrite(&(seg.block_size), sizeof(uint64_t), 1, mem_file);
        tempValue = seg.physical_base.getCompressed();
        storedBytes += fwrite(&tempValue, sizeof(uint64_t), 1, mem_file);
        storedBytes += fwrite(&(seg.access_flags), sizeof(uint8_t), 1, mem_file);
        
        // add some padding after the metadata, so that debugging gets easier as the blocks are aligned.
        tempValue = 0xcafecafecafecafe;
        storedBytes += fwrite(&tempValue, sizeof(uint8_t)*3, 1, mem_file);

        for(uint64_t vAddr=seg.virtual_base; vAddr < seg.virtual_limit; vAddr += seg.block_size) {
            // translating the virtual address
            physical_addr_t pa = seg.getPhysicalAddr(vAddr);

            // Dump only data, that is of this node
            // Other node's addresses are inaccessible from this node. Hence, the TOP program of their nodes,
            // have to initialize their own dumpMemory.
            if(nodeID != pa.getNodeId()) {
            BASIM_INFOMSG("DRAM Dump: NodeID %ld: skipping: vAddr: 0x%lx, pAddr 0x%lx, nodeID: %ld", nodeID, (uint64_t)vAddr, pa.getCompressed(), pa.getNodeId());
                continue;
            }

            // Translate the physical address of the simulator to the host address, where we can actually find the data
            uint64_t pAddr = pa.getCompressed();
            common_addr hostAddr = mapPA2SA(pAddr, 1);
            auto dst = reinterpret_cast<word_t*>(hostAddr.addr);
            BASIM_INFOMSG("DRAM Dump: NodeID %ld: vAddr: 0x%lx, pAddr 0x%lx, hostAddr: %p, block_size: %ld", nodeID, (uint64_t)vAddr, pAddr, dst, seg.block_size);

            // store the data in the file
            storedBytes += fwrite(dst, sizeof(uint8_t), std::min(seg.block_size, seg.virtual_limit-vAddr), mem_file);
        }
    }
    fclose(mem_file);
    BASIM_INFOMSG("DRAM Dump: NodeID %ld: Dump complete. Stored %ld Bytes", nodeID, storedBytes);
    return storedBytes;
}

size_t BASimUDRuntime_t::loadMemoryTranslation(std::string filename, uint64_t nodeID, void* dumpVA) {
    size_t loadedBytes;
    filename += std::to_string(nodeID) + ".dram.dat";
    FILE* mem_file = fopen(filename.c_str(), "rb");
    UPDOWN_ERROR_IF(!mem_file, "DRAM Load: NodeID %ld: Could not open %s", nodeID, filename.c_str());

    // Read 'F' to indicate dump by Fastsim
    char dump_type;
    loadedBytes = fread(&dump_type, sizeof(char), 1, mem_file);
    UPDOWN_ERROR_IF(dump_type != 'F', "DRAM dump load failed! Not a FastSim dump file!\n");

    // Read 'D' to indicate DRAM dump
    loadedBytes += fread(&dump_type, sizeof(char), 1, mem_file);
    UPDOWN_ERROR_IF(dump_type != 'D', "DRAM dump load failed! Not a DRAM dump file!\n");

    // Read version number
    uint16_t version;
    loadedBytes += fread(&version, sizeof(uint16_t), 1, mem_file);
    UPDOWN_ERROR_IF(version != 1, "DRAM dump load failed! Incorrect format version!\n");

    // Read number of entries for the private and global segments
    size_t nPrivateSegments, nGlobalSegments;
    loadedBytes = fread(&nPrivateSegments, sizeof(size_t), 1, mem_file);
    loadedBytes = fread(&nGlobalSegments, sizeof(size_t), 1, mem_file);

    for(uint64_t seg=0; seg<nGlobalSegments; ++seg) {
        uint64_t metaPos = ftell(mem_file);
        BASIM_INFOMSG("DRAM Load: NodeID %ld: Metadata position: %ld (0x%lx)\n", nodeID, metaPos, metaPos);

        // Read the metadata
        basim::Addr vBase, vLimit, pBase;
        uint64_t swizzleMask, blockSize;
        uint8_t accessFlags;
        loadedBytes += fread(&vBase, sizeof(basim::Addr), 1, mem_file);
        loadedBytes += fread(&vLimit, sizeof(basim::Addr), 1, mem_file);
        loadedBytes += fread(&swizzleMask, sizeof(uint64_t), 1, mem_file);
        loadedBytes += fread(&blockSize, sizeof(uint64_t), 1, mem_file);
        loadedBytes += fread(&pBase, sizeof(basim::Addr), 1, mem_file);
        loadedBytes += fread(&accessFlags, sizeof(uint8_t), 1, mem_file);

        // skip over the padding fields (The coffee from above)
        fseek(mem_file, 3, SEEK_CUR);
        BASIM_INFOMSG("DRAM Load: NodeID %ld: Found metadata: vBase: 0x%lx, vLimit: 0x%lx, swizzleMask: 0x%lx, pAddr: 0x%lx, blockSize: %ld, accessFlags: %d\n", nodeID, vBase, vLimit, swizzleMask, pBase, blockSize, accessFlags);


        // get access to the translation memory
        basim::TranslationMemoryPtr transmem = this->uds[0]->getTranslationMem();

        for(basim::Addr vAddr=vBase; vAddr<vLimit; vAddr+=blockSize) {

            // translating the virtual address to the host's address
            uint64_t translationSize = std::min(blockSize, vLimit-vAddr);

            if(vBase > reinterpret_cast<basim::Addr>(dumpVA)) {
                BASIM_INFOMSG("DRAM Load: Returning early as we find unallocated blocks\n", nodeID, vBase);
                fclose(mem_file);

                return loadedBytes;
            }

            uint64_t pAddr = transmem->translate_va2pa_global(vAddr, translationSize/sizeof(UpDown::word_t));
            UPDOWN_ERROR_IF(pAddr == transmem->INVALID_ADDR, "DRAM Load: NodeID: %ld: Could not translate vAddr: 0x%lx, vLimit: 0x%lx, translationSize: %ld Bytes", nodeID, vAddr, vLimit, translationSize);
            auto pa = physical_addr_t(pAddr);

            // Read only data, that is for this node
            // Other node's addresses are inaccessible from this node. Hence, the TOP program of their nodes,
            // have to initialize their own dumpRead.
            if(nodeID != pa.getNodeId()) {
                BASIM_INFOMSG("DRAM Load: NodeID %ld: skipping: vAddr: 0x%lx as data is not on current node, vLimit: 0x%lx, pAddr 0x%lx, nodeID: %ld\n", nodeID, (uint64_t)vAddr, vLimit, pa.getCompressed(), pa.getNodeId());
                // fseek(mem_file, translationSize, SEEK_CUR);
                continue;
            }

            if(vBase != reinterpret_cast<basim::Addr>(dumpVA)) {
                BASIM_INFOMSG("DRAM Load: NodeID %ld: skipping: vAddr: 0x%lx as it is not the target, vLimit: 0x%lx, pAddr 0x%lx, nodeID: %ld\n", nodeID, (uint64_t)vAddr, vLimit, pa.getCompressed(), pa.getNodeId());
                fseek(mem_file, translationSize, SEEK_CUR);
                continue;
            }

            // translate the physical address to the host's address
            auto sAddr = reinterpret_cast<word_t*>(mapPA2SA(pa.getCompressed(), 1).addr);

            BASIM_INFOMSG("DRAM Load Executed: NodeID %ld: vAddr: 0x%lx, pAddr 0x%lx, hostAddr: %p, block_size: %ld\n", nodeID, (uint64_t)vAddr, pa.getCompressed(), sAddr, blockSize);

            // read 1 block from the file
            loadedBytes += fread(sAddr, sizeof(uint8_t), translationSize, mem_file);
        }
    }
    BASIM_INFOMSG("DRAM Load: NodeID %ld: Dump loading complete. Loaded %ld Bytes\n", nodeID, loadedBytes);
    return loadedBytes;
}

  
void BASimUDRuntime_t::dumpMemory(const char* filename, void* vaddr, uint64_t size){
  FILE* mem_file = fopen(filename, "wb");
  UPDOWN_ERROR_IF(!mem_file, "Could not open %s", filename);

  // Use API to access mm_malloced area
  uint64_t offset = reinterpret_cast<uint64_t>(vaddr) - reinterpret_cast<uint64_t>(BaseAddrs.mmaddr);
  auto *data = (uint8_t*)malloc(size * sizeof(uint8_t));
  this->mm2t_memcpy(offset, data, size);

  fseek(mem_file, 0, SEEK_SET);
  // Write 'F' to indicate dump by Fastsim
  fwrite("F", sizeof(char), 1, mem_file);
  // Write 'D' to indicate DRAM dump
  fwrite("D", sizeof(char), 1, mem_file);
  // Write dump start file offset
  //                                F   D dump_start_file_offset  vaddr  size
  uint64_t dump_start_file_offset = 1 + 1     + 8 +                8     + 8;
  fwrite(&dump_start_file_offset, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump start file offset: %lu", dump_start_file_offset);
  // Write dump vaddr
  fwrite(&vaddr, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump vaddr: %p", vaddr);
  // Write dump size
  fwrite(&size, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump size: %lu", size);
  // Write size bytes into mem_file
  fwrite(data, sizeof(uint8_t), size, mem_file);

  fclose(mem_file);
  free(data);
}

std::pair<void *, uint64_t> BASimUDRuntime_t::loadMemory(const char* filename, void* vaddr, uint64_t size) {
  size_t loadedBytes; // to prevent compiler warnings


  FILE* mem_file = fopen(filename, "rb");
  UPDOWN_ERROR_IF(!mem_file, "Could not open %s", filename);

  fseek(mem_file, 0, SEEK_SET);
  // Read 'F' to indicate dump by Fastsim
  char dump_type;
  loadedBytes = fread(&dump_type, sizeof(char), 1, mem_file);
  UPDOWN_ERROR_IF(dump_type != 'F', "DRAM dump load failed! Not a FastSim dump file!\n");
  // Read 'D' to indicate DRAM dump
  loadedBytes = fread(&dump_type, sizeof(char), 1, mem_file);
  UPDOWN_ERROR_IF(dump_type != 'D', "DRAM dump load failed! Not a DRAM dump file!\n");
  // Read dump start file offset
  uint64_t dump_start_file_offset;
  loadedBytes = fread(&dump_start_file_offset, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump start file offset: %lu", dump_start_file_offset);
  // Read dump vaddr
  uint64_t dump_vaddr;
  loadedBytes = fread(&dump_vaddr, sizeof(uint64_t), 1, mem_file);
  if (vaddr == nullptr) {
    vaddr = reinterpret_cast<void *>(dump_vaddr);
    BASIM_INFOMSG("DRAM Dump vaddr (from dump file): %p", vaddr);
  } else {
    BASIM_INFOMSG("DRAM Dump vaddr (user specified): %p", vaddr);
  }
  // Read dump size
  uint64_t dump_size;
  loadedBytes = fread(&dump_size, sizeof(uint64_t), 1, mem_file);
  if (vaddr == nullptr || size == 0) {
    size = dump_size;
    BASIM_INFOMSG("DRAM Dump size (from dump file): %lu", size);
  } else {
    BASIM_INFOMSG("DRAM Dump size (user specified): %lu", size);
  }
  // Read size bytes into mem_file
  fseek(mem_file, dump_start_file_offset, SEEK_SET);
  uint8_t *data = (uint8_t*)malloc(size * sizeof(uint8_t));
  loadedBytes = fread(data, sizeof(uint8_t), size, mem_file);

  // Use API to access mm_malloced area
  if (this->mm_malloc_at_addr(vaddr, size) == nullptr) { // allocate memory
    BASIM_ERROR("DRAM dump load failed! Cannot allocate memory at (%p, %lu)", vaddr, size);
  }
  uint64_t offset = reinterpret_cast<uint64_t>(vaddr) - reinterpret_cast<uint64_t>(BaseAddrs.mmaddr);
  this->t2mm_memcpy(offset, data, size);

  fclose(mem_file);
  free(data);

  return std::make_pair(vaddr, size);
}

void BASimUDRuntime_t::dumpLocalMemory(const char* filename, networkid_t start_nwid, uint64_t num_lanes) {
  FILE* spd_file = fopen(filename, "wb");
  if (!spd_file) {
    printf("Could not open %s\n", filename);
    exit(1);
  }

  uint64_t lane_lm_size = DEF_SPMEM_BANK_SIZE;
  uint64_t total_lm_size;
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    // all LMs
    total_lm_size = lane_lm_size * this->MachineConfig.NumLanes * this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes;
    num_lanes = this->MachineConfig.NumLanes * this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes;
  } else {
    // selected LMs
    total_lm_size = lane_lm_size * num_lanes;
  }
  uint8_t *data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
  basim::Addr start_addr = (uint64_t)BaseAddrs.spaddr;
  uint64_t lm_offset = 0;

  for (uint32_t i = start_nwid.get_NetworkId_UdName(); i < start_nwid.get_NetworkId_UdName() + num_lanes; i++) {
    uds[i / DEF_NUM_LANES]->readScratchPadBank(i % DEF_NUM_LANES, &data[lm_offset]);
    lm_offset += DEF_SPMEM_BANK_SIZE;
  }

  fseek(spd_file, 0, SEEK_SET);
  // Write 'F' to indicate dump by Fastsim
  fwrite("F", sizeof(char), 1, spd_file);
  // Write 'L' to indicate LM dump
  fwrite("L", sizeof(char), 1, spd_file);
  // Write dump start file offset
  uint64_t dump_start_file_offset = 1 + 1 + 8 + 8 + 8 + 8;
  fwrite(&dump_start_file_offset, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump start file offset: %lu", dump_start_file_offset);
  // Write dump start nwid (ud_name only)
  uint64_t dump_nwid = start_nwid.get_NetworkId_UdName();
  fwrite(&dump_nwid, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump start nwid: %lu", dump_nwid);
  // Write num lanes dumped
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    num_lanes = this->MachineConfig.NumLanes * this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes;
  }
  fwrite(&num_lanes, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump num lanes: %lu", num_lanes);
  // Write LM size per lane
  fwrite(&lane_lm_size, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump size per lane: %lu", lane_lm_size);
  // Write size bytes into mem_file
  fwrite(data, sizeof(uint8_t), total_lm_size, spd_file);
  fclose(spd_file);

  free(data);
}

std::pair<networkid_t, uint64_t> BASimUDRuntime_t::loadLocalMemory(const char* filename, networkid_t start_nwid, uint64_t num_lanes) {
  size_t loadedBytes; // just to prevent compiler warnings
  FILE* spd_file = fopen(filename, "rb");
  if (!spd_file) {
    printf("Could not open %s\n", filename);
    exit(1);
  }

  fseek(spd_file, 0, SEEK_SET);
  // Read 'F' to indicate dump by Fastsim
  char dump_type;
  loadedBytes = fread(&dump_type, sizeof(char), 1, spd_file);
  UPDOWN_ERROR_IF(dump_type != 'F', "DRAM dump load failed! Not a FastSim dump file!\n");
  // Read 'L' to indicate LM dump
  loadedBytes = fread(&dump_type, sizeof(char), 1, spd_file);
  UPDOWN_ERROR_IF(dump_type != 'L', "DRAM dump load failed! Not a LM dump file!\n");
  // Read dump start file offset
  uint64_t dump_start_file_offset;
  loadedBytes = fread(&dump_start_file_offset, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump start file offset: %lu", dump_start_file_offset);
  // Read dump start nwid (ud_name only)
  uint64_t dump_start_nwid_raw;
  loadedBytes = fread(&dump_start_nwid_raw, sizeof(uint64_t), 1, spd_file);
  networkid_t dump_start_nwid(dump_start_nwid_raw, false, 0);
  BASIM_INFOMSG("LM Dump start nwid (from dump file): %lu", dump_start_nwid_raw);
  // Read num lanes dumped
  uint64_t dump_num_lanes;
  loadedBytes = fread(&dump_num_lanes, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump num lanes (from dump file): %lu", dump_num_lanes);
  // Read LM size per lane
  uint64_t lane_lm_size;
  loadedBytes = fread(&lane_lm_size, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump size per lane (from dump file): %lu", lane_lm_size);

  // Copy it lm by lm
  fseek(spd_file, dump_start_file_offset, SEEK_SET);
  uint8_t *data = nullptr;
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    // LM specified from the dump
    uint64_t total_lm_size = dump_num_lanes * lane_lm_size;
    data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
    loadedBytes = fread(data, sizeof(uint8_t), total_lm_size, spd_file);
    uint64_t lm_offset = 0;
    for (uint32_t i = dump_start_nwid.get_NetworkId_UdName(); i < dump_start_nwid.get_NetworkId_UdName() + dump_num_lanes; i++) {
      uds[i / DEF_NUM_LANES]->writeScratchPadBank(i % DEF_NUM_LANES, &data[lm_offset]);
      lm_offset += DEF_SPMEM_BANK_SIZE;
    }
  } else {
    // all LMs
    uint64_t total_lm_size = num_lanes * DEF_SPMEM_BANK_SIZE;
    data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
    loadedBytes = fread(data, sizeof(uint8_t), total_lm_size, spd_file);
    uint64_t lm_offset = 0;
    for (uint32_t i = start_nwid.get_NetworkId_UdName(); i < start_nwid.get_NetworkId_UdName() + num_lanes; i++) {
      uds[i / DEF_NUM_LANES]->writeScratchPadBank(i % DEF_NUM_LANES, &data[lm_offset]);
      lm_offset += DEF_SPMEM_BANK_SIZE;
    }
  }

  fclose(spd_file);
  free(data);

  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    return std::make_pair(dump_start_nwid, dump_num_lanes);
  } else {
    return std::make_pair(start_nwid, num_lanes);
  }
}

void BASimUDRuntime_t::reset_stats(uint32_t ud_id, uint8_t lane_id){
  this->uds[ud_id]->resetStats(lane_id);
}

void BASimUDRuntime_t::reset_stats(uint32_t ud_id){
  this->uds[ud_id]->resetStats();
}

void BASimUDRuntime_t::reset_stats(){
#ifndef GEM5_MODE
  #pragma omp parallel for // ud level parallelism
  for (int ud = 0; ud < total_uds; ud++)
    this->uds[ud]->resetStats();
#else
  for (int ud = 0; ud < total_uds; ud++)
    this->uds[ud]->resetStats();
#endif
}

void BASimUDRuntime_t::update_stats(uint32_t lane_num) {
  uint8_t lane_id = lane_num % 64;
  uint32_t ud_id = lane_num / 64;
  this->update_stats(ud_id, lane_id);
}

void BASimUDRuntime_t::update_stats(uint32_t ud_id, uint8_t lane_num) {

  const basim::LaneStats* loc_stats = uds[ud_id]->getLaneStats(lane_num);
  uint32_t lane_id = lane_num; 
  this->simStats[ud_id][lane_id].cycle_count = loc_stats->cycle_count;
  this->simStats[ud_id][lane_id].inst_count = loc_stats->inst_count;  
  this->simStats[ud_id][lane_id].tran_count = loc_stats->tran_count;
  this->simStats[ud_id][lane_id].thread_count = loc_stats->thread_count;
  this->simStats[ud_id][lane_id].max_thread_count = loc_stats->max_thread_count;
  this->simStats[ud_id][lane_id].cycles_gt128th = loc_stats->cycles_gt128th;
  this->simStats[ud_id][lane_id].inst_count_atomic = loc_stats->inst_count_atomic;
  this->simStats[ud_id][lane_id].inst_count_bitwise = loc_stats->inst_count_bitwise;
  this->simStats[ud_id][lane_id].inst_count_ctrlflow = loc_stats->inst_count_ctrlflow;
  this->simStats[ud_id][lane_id].inst_count_datmov = loc_stats->inst_count_datmov; 
  this->simStats[ud_id][lane_id].inst_count_ev = loc_stats->inst_count_ev;
  this->simStats[ud_id][lane_id].inst_count_fparith = loc_stats->inst_count_fparith;
  this->simStats[ud_id][lane_id].inst_count_hash = loc_stats->inst_count_hash;
  this->simStats[ud_id][lane_id].inst_count_intarith = loc_stats->inst_count_intarith;
  this->simStats[ud_id][lane_id].inst_count_intcmp = loc_stats->inst_count_intcmp;
  this->simStats[ud_id][lane_id].inst_count_msg = loc_stats->inst_count_msg;
  this->simStats[ud_id][lane_id].inst_count_threadctrl = loc_stats->inst_count_threadctrl;
  this->simStats[ud_id][lane_id].inst_count_tranctrl = loc_stats->inst_count_tranctrl;
  this->simStats[ud_id][lane_id].inst_count_vec = loc_stats->inst_count_vec;
  this->simStats[ud_id][lane_id].tran_count_basic = loc_stats->tran_count_basic;
  this->simStats[ud_id][lane_id].tran_count_majority = loc_stats->tran_count_majority;
  this->simStats[ud_id][lane_id].tran_count_default = loc_stats->tran_count_default;
  this->simStats[ud_id][lane_id].tran_count_epsilon = loc_stats->tran_count_epsilon;
  this->simStats[ud_id][lane_id].tran_count_common = loc_stats->tran_count_common;
  this->simStats[ud_id][lane_id].tran_count_flagged = loc_stats->tran_count_flagged;
  this->simStats[ud_id][lane_id].tran_count_refill = loc_stats->tran_count_refill;
  this->simStats[ud_id][lane_id].tran_count_event = loc_stats->tran_count_event;
  this->simStats[ud_id][lane_id].tran_count_other_node = loc_stats->tran_count_other_node;
  this->simStats[ud_id][lane_id].tran_bytes_other_node = loc_stats->tran_bytes_other_node;
  this->simStats[ud_id][lane_id].dram_store_count_other_node = loc_stats->dram_store_count_other_node;
  this->simStats[ud_id][lane_id].dram_load_count_other_node = loc_stats->dram_load_count_other_node;
  this->simStats[ud_id][lane_id].dram_store_bytes_other_node = loc_stats->dram_store_bytes_other_node;
  this->simStats[ud_id][lane_id].dram_load_bytes_other_node = loc_stats->dram_load_bytes_other_node;
  this->simStats[ud_id][lane_id].dram_store_ack_count_other_node = loc_stats->dram_store_ack_count_other_node;
  this->simStats[ud_id][lane_id].dram_load_ack_count_other_node = loc_stats->dram_load_ack_count_other_node;
  this->simStats[ud_id][lane_id].dram_store_ack_bytes_other_node = loc_stats->dram_store_ack_bytes_other_node;
  this->simStats[ud_id][lane_id].dram_load_ack_bytes_other_node = loc_stats->dram_load_ack_bytes_other_node;
#ifdef DETAIL_STATS
  this->simStats[ud_id][lane_id].max_inst_count_per_event = loc_stats->max_inst_per_event;
  this->simStats[ud_id][lane_id].max_inst_count_per_tx = loc_stats->max_inst_per_tx;
#endif
  this->simStats[ud_id][lane_id].lm_load_bytes = loc_stats->lm_load_bytes;
  this->simStats[ud_id][lane_id].lm_store_bytes = loc_stats->lm_store_bytes;
  this->simStats[ud_id][lane_id].lm_load_count = loc_stats->lm_load_count;
  this->simStats[ud_id][lane_id].lm_store_count = loc_stats->lm_store_count;
  this->simStats[ud_id][lane_id].dram_load_bytes = loc_stats->dram_load_bytes;
  this->simStats[ud_id][lane_id].dram_store_bytes = loc_stats->dram_store_bytes;
  this->simStats[ud_id][lane_id].dram_load_count = loc_stats->dram_load_count;
  this->simStats[ud_id][lane_id].dram_store_count = loc_stats->dram_store_count;
  this->simStats[ud_id][lane_id].eventq_len_max = loc_stats->eventq_len_max;
  this->simStats[ud_id][lane_id].opbuff_len_max = loc_stats->opbuff_len_max;
  //for (int i = 0; i < 16; i++) {
  //  this->simStats[ud_id][lane_num].user_counter[i] = loc_stats->user_counter[i];
  //}
}

struct BASimStats& BASimUDRuntime_t::get_stats(uint32_t ud_id, uint8_t lane_num){
  update_stats(ud_id, lane_num);
  return this->simStats[ud_id][lane_num];
}

struct BASimStats& BASimUDRuntime_t::get_stats(uint32_t lane_num){
  uint8_t lane_id = lane_num % 64;
  uint32_t ud_id = lane_num / 64;
  return this->get_stats(ud_id, lane_id);
}

void BASimUDRuntime_t::print_stats(uint32_t lane_num){
  uint8_t lane_id = lane_num % 64;
  uint32_t ud_id = lane_num / 64;
  print_stats(ud_id, lane_id);
}

void BASimUDRuntime_t::print_stats(uint32_t ud_id, uint8_t lane_num) {
  const int wid = 10;
  const basim::LaneStats* lnstats = uds[ud_id]->getLaneStats(lane_num);

  printf("[BASIM_GLOBAL]: Curr_Sim_Cycle:%lu\n", this->simTicks);
  printf("[UD%d-L%d] Cycles               =%lu\n", ud_id, lane_num, static_cast<uint64_t>(lnstats->cycle_count));
  printf("[UD%d-L%d] InstructionCount     =%lu\n", ud_id, lane_num, lnstats->inst_count); 
  printf("[UD%d-L%d] TransitionCount      =%lu\n", ud_id, lane_num, lnstats->tran_count);
  printf("[UD%d-L%d] ThreadCount          =%lu\n", ud_id, lane_num, lnstats->thread_count);
  printf("[UD%d-L%d] MaxThreadCount       =%lu\n", ud_id, lane_num, lnstats->max_thread_count);
  printf("[UD%d-L%d] Cycles (>128threads) =%lu\n", ud_id, lane_num, lnstats->cycles_gt128th);
  printf("[UD%d-L%d] AtomicInstructions   =%lu\n", ud_id, lane_num, lnstats->inst_count_atomic);
  printf("[UD%d-L%d] BitWiseInstructions  =%lu\n", ud_id, lane_num, lnstats->inst_count_bitwise);
  printf("[UD%d-L%d] CtrlFlowInstructions =%lu\n", ud_id, lane_num, lnstats->inst_count_ctrlflow);
  printf("[UD%d-L%d] DataMovInstructions  =%lu\n", ud_id, lane_num, lnstats->inst_count_datmov);
  printf("[UD%d-L%d] EvInstructions       =%lu\n", ud_id, lane_num, lnstats->inst_count_ev);
  printf("[UD%d-L%d] FPArithInstructions  =%lu\n", ud_id, lane_num, lnstats->inst_count_fparith);
  printf("[UD%d-L%d] HashInstructions     =%lu\n", ud_id, lane_num, lnstats->inst_count_hash);
  printf("[UD%d-L%d] IntArithInstructions =%lu\n", ud_id, lane_num, lnstats->inst_count_intarith);
  printf("[UD%d-L%d] IntCompInstructions  =%lu\n", ud_id, lane_num, lnstats->inst_count_intcmp);
  printf("[UD%d-L%d] MsgInstructions      =%lu\n", ud_id, lane_num, lnstats->inst_count_msg);
  printf("[UD%d-L%d] MsgInstructions(Mem) =%lu\n", ud_id, lane_num, lnstats->inst_count_msg_mem);
  printf("[UD%d-L%d] MsgInstructions(Lane)=%lu\n", ud_id, lane_num, lnstats->inst_count_msg_lane);
  printf("[UD%d-L%d] ThrdCtrlInstructions =%lu\n", ud_id, lane_num, lnstats->inst_count_threadctrl);
  printf("[UD%d-L%d] TranCtrlInstructions =%lu\n", ud_id, lane_num, lnstats->inst_count_tranctrl);
  printf("[UD%d-L%d] VectorInstructions   =%lu\n", ud_id, lane_num, lnstats->inst_count_vec);
  printf("[UD%d-L%d] BasicTransitions     =%lu\n", ud_id, lane_num, lnstats->tran_count_basic);
  printf("[UD%d-L%d] MajorityTransitions  =%lu\n", ud_id, lane_num, lnstats->tran_count_majority);
  printf("[UD%d-L%d] DefaultTransitions   =%lu\n", ud_id, lane_num, lnstats->tran_count_default);
  printf("[UD%d-L%d] EpsilonTransitions   =%lu\n", ud_id, lane_num, lnstats->tran_count_epsilon);
  printf("[UD%d-L%d] CommonTransitions    =%lu\n", ud_id, lane_num, lnstats->tran_count_common);
  printf("[UD%d-L%d] FlaggedTransitions   =%lu\n", ud_id, lane_num, lnstats->tran_count_flagged);
  printf("[UD%d-L%d] RefillTransitions    =%lu\n", ud_id, lane_num, lnstats->tran_count_refill);
  printf("[UD%d-L%d] EventTransitions     =%lu\n", ud_id, lane_num, lnstats->tran_count_event);
  printf("[UD%d-L%d] MessagesNodeCount    =%lu\n", ud_id, lane_num, lnstats->tran_count_other_node);
  printf("[UD%d-L%d] MessagesNodeBytes    =%lu\n", ud_id, lane_num, lnstats->tran_bytes_other_node);
  printf("[UD%d-L%d] DRAMStoreNodeCount   =%lu\n", ud_id, lane_num, lnstats->dram_store_count_other_node);
  printf("[UD%d-L%d] DRAMStoreNodeBytes   =%lu\n", ud_id, lane_num, lnstats->dram_store_bytes_other_node);
  printf("[UD%d-L%d] DRAMLoadNodeCount    =%lu\n", ud_id, lane_num, lnstats->dram_load_count_other_node);
  printf("[UD%d-L%d] DRAMLoadNodeBytes    =%lu\n", ud_id, lane_num, lnstats->dram_load_bytes_other_node);
  printf("[UD%d-L%d] DRAMStoreNodeAckCount   =%lu\n", ud_id, lane_num, lnstats->dram_store_ack_count_other_node);
  printf("[UD%d-L%d] DRAMStoreNodeAckBytes   =%lu\n", ud_id, lane_num, lnstats->dram_store_ack_bytes_other_node);
  printf("[UD%d-L%d] DRAMLoadNodeAckCount    =%lu\n", ud_id, lane_num, lnstats->dram_load_ack_count_other_node);
  printf("[UD%d-L%d] DRAMLoadNodeAckBytes    =%lu\n", ud_id, lane_num, lnstats->dram_load_ack_bytes_other_node);
#ifdef DETAIL_STATS
  printf("[UD%d-L%d] MaxInstCountPerEvent =%lu\n", ud_id, lane_num, lnstats->max_inst_per_event);
  printf("[UD%d-L%d] MaxInstCountPerTx    =%lu\n", ud_id, lane_num, lnstats->max_inst_per_tx);
#endif
  printf("[UD%d-L%d] LMLoadBytes          =%lu\n", ud_id, lane_num, lnstats->lm_load_bytes);
  printf("[UD%d-L%d] LMStoreBytes         =%lu\n", ud_id, lane_num, lnstats->lm_store_bytes);
  printf("[UD%d-L%d] LMLoadCount          =%lu\n", ud_id, lane_num, lnstats->lm_load_count);
  printf("[UD%d-L%d] LMStoreCount         =%lu\n", ud_id, lane_num, lnstats->lm_store_count);
  printf("[UD%d-L%d] DRAMLoadBytes        =%lu\n", ud_id, lane_num, lnstats->dram_load_bytes);
  printf("[UD%d-L%d] DRAMStoreBytes       =%lu\n", ud_id, lane_num, lnstats->dram_store_bytes);
  printf("[UD%d-L%d] DRAMLoadCount        =%lu\n", ud_id, lane_num, lnstats->dram_load_count);
  printf("[UD%d-L%d] DRAMStoreCount       =%lu\n", ud_id, lane_num, lnstats->dram_store_count);
  printf("[UD%d-L%d] MessageBytes         =%lu\n", ud_id, lane_num, lnstats->message_bytes);
  printf("[UD%d-L%d] EventQLenMax         =%lu\n", ud_id, lane_num, lnstats->eventq_len_max);
  printf("[UD%d-L%d] OperandQueueLenMax   =%lu\n", ud_id, lane_num, lnstats->opbuff_len_max);


  //for (int i = 0; i < 16; i++) {
  //  std::printf("[UD%d-L%d] user_counter%2d      = %*ld\n", ud_id, lane_num, i,
  //              wid, this->simStats[ud_id][lane_num].user_counter[i]);
  //}
}

/* Print the current simulation time in cycles  */
void BASimUDRuntime_t::print_curr_cycle(void){
  printf("[BASIM_GLOBAL]: Curr_Sim_Cycle:%lu\n", this->simTicks);
}

/* Reset the current simulation time to 0 cycles  */
void BASimUDRuntime_t::reset_curr_cycle(void){
  if(pthread_mutex_trylock(&mutex) == 0) {
    this->simTicks = 0;
    this->num_start_exe = 0;
  }
  pthread_mutex_unlock(&mutex);
  printf("[BASIM_GLOBAL]: Reset Curr_Sim_Cycle:%lu\n", this->simTicks);
}

void BASimUDRuntime_t::print_node_stats(uint32_t nodeID) {
  printf("[BASIM_GLOBAL]: Curr_Sim_Cycle:%lu\n", this->simTicks);
    #ifdef ASST_FASTSIM
        uint32_t upperLimit = 1;
    #else
        uint32_t upperLimit = this->MachineConfig.NumNodes;
    #endif

    #if defined(NETWORK_STATS)
    printf("[Node%d] PeakTotalCrossNodeCount  = %lu\n", nodeID, this->simNodeStats[nodeID].max_counts[0]->load());
    printf("[Node%d] PeakTotalCrossNodeBytes  = %lu\n", nodeID, this->simNodeStats[nodeID].max_bytes[0]->load());
    printf("[Node%d] MaxQueueSize  = %lu\n", nodeID, this->simNodeStats[nodeID].max_queue_size[0]->load());
    printf("[Node%d] AvgQueueSize  = %.2f\n", nodeID, this->simNodeStats[nodeID].total_queue_size[0]->load()/num_start_exe);

    for(uint32_t dstNodeID=0; dstNodeID<upperLimit; ++dstNodeID) {
        if(nodeID == dstNodeID) {
          continue;
        }
        
        printf("[Node%d->%d] TotalNodeCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].total_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] TotalNodeBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].total_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] MessagesNodeCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].tran_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] MessagesNodeBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].tran_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMStoreNodeCount = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_store_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMStoreNodeBytes = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_store_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMLoadNodeCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_load_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMLoadNodeBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_load_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMStoreNodeAckCount = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_store_ack_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMStoreNodeAckBytes = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_store_ack_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMLoadNodeAckCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_load_ack_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] DRAMLoadNodeAckBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_load_ack_bytes_other_node[dstNodeID]->load());

        printf("[Node%d->%d] PeakTotalNodeCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_total_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakTotalNodeBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_total_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakMessagesNodeCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_tran_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakMessagesNodeBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_tran_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMStoreNodeCount = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_store_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMStoreNodeBytes = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_store_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMLoadNodeCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_load_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMLoadNodeBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_load_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMStoreNodeAckCount = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_store_ack_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMStoreNodeAckBytes = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_store_ack_bytes_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMLoadNodeAckCount  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_load_ack_count_other_node[dstNodeID]->load());
        printf("[Node%d->%d] PeakDRAMLoadNodeAckBytes  = %lu\n", nodeID, dstNodeID, this->simNodeStats[nodeID].max_dram_load_ack_bytes_other_node[dstNodeID]->load());

        printf("[Node%d->%d] TotalPacketSizeHistogram  = [%lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu]\n", nodeID, dstNodeID, this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][0]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][1]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][2]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][3]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][4]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][5]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][6]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][7]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][8]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][9]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][10]->load(), this->simNodeStats[nodeID].total_packet_size_other_node_histogram[dstNodeID][11]->load());
        printf("[Node%d->%d] TranPacketSizeHistogram  = [%lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu]\n", nodeID, dstNodeID, this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][0]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][1]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][2]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][3]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][4]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][5]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][6]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][7]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][8]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][9]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][10]->load(), this->simNodeStats[nodeID].tran_packet_size_other_node_histogram[dstNodeID][11]->load());
        printf("[Node%d->%d] DramLoadPacketSizeHistogram  = [%lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu]\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][0]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][1]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][2]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][3]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][4]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][5]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][6]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][7]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][8]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][9]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][10]->load(), this->simNodeStats[nodeID].dram_load_packet_size_other_node_histogram[dstNodeID][11]->load());
        printf("[Node%d->%d] DramLoadAckPacketSizeHistogram  = [%lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu]\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][0]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][1]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][2]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][3]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][4]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][5]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][6]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][7]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][8]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][9]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][10]->load(), this->simNodeStats[nodeID].dram_load_ack_packet_size_other_node_histogram[dstNodeID][11]->load());
        printf("[Node%d->%d] DramStorePacketSizeHistogram  = [%lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu]\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][0]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][1]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][2]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][3]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][4]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][5]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][6]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][7]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][8]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][9]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][10]->load(), this->simNodeStats[nodeID].dram_store_packet_size_other_node_histogram[dstNodeID][11]->load());
        printf("[Node%d->%d] DramStoreAckPacketSizeHistogram  = [%lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu]\n", nodeID, dstNodeID, this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][0]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][1]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][2]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][3]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][4]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][5]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][6]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][7]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][8]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][9]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][10]->load(), this->simNodeStats[nodeID].dram_store_ack_packet_size_other_node_histogram[dstNodeID][11]->load());

    }
    #endif
  // print memory stack stats
  for(uint32_t stid = 0; stid < this->MachineConfig.NumStacks; stid++){
    const basim::StackStats* ststats = udMems[nodeID]->getStackStats(stid);
    printf("[Node%d-S%d] DRAMStackLoadBytes           =%lu\n", nodeID, stid, ststats->dram_load_bytes);
    printf("[Node%d-S%d] DRAMStackStoreBytes          =%lu\n", nodeID, stid, ststats->dram_store_bytes);
    printf("[Node%d-S%d] DRAMStackLoadCount           =%lu\n", nodeID, stid, ststats->dram_load_count);
    printf("[Node%d-S%d] DRAMStackStoreCount          =%lu\n", nodeID, stid, ststats->dram_store_count);
    printf("[Node%d-S%d] DRAMStackPeakLoadBytes       =%lu\n", nodeID, stid, ststats->peak_dram_load_bytes);
    printf("[Node%d-S%d] DRAMStackPeakStoreBytes      =%lu\n", nodeID, stid, ststats->peak_dram_store_bytes);
    printf("[Node%d-S%d] DRAMStackPeakLoadCount       =%lu\n", nodeID, stid, ststats->peak_dram_load_count);
    printf("[Node%d-S%d] DRAMStackPeakStoreCount      =%lu\n", nodeID, stid, ststats->peak_dram_store_count);
    printf("[Node%d-S%d] DRAMStackPeakLoadStoreCount  =%lu\n", nodeID, stid, ststats->peak_dram_load_store_count);
  }
}

void BASimUDRuntime_t::reset_node_stats() {
    #ifdef ASST_FASTSIM
        uint32_t upperLimit = 1;
    #else
        uint32_t upperLimit = this->MachineConfig.NumNodes;
    #endif

    for(uint32_t nodeID = 0; nodeID < upperLimit; nodeID++){
      this->simNodeStats[nodeID].reset(upperLimit);
      // print memory stack stats
      for(uint32_t stid = 0; stid < this->MachineConfig.NumStacks; stid++){
        basim::StackStats* ststats = udMems[nodeID]->getStackStats(stid);
        ststats->reset();
      }

  }
}

void BASimUDRuntime_t::reset_all_stats() {
  this->reset_stats();  // reset lane stats
  this->reset_node_stats(); // reset node and dram stack stats
  this->reset_curr_cycle(); // reset ticks
}



#ifdef INST_HIST
void BASimUDRuntime_t::print_inst_hist(const char* filename){
  std::ofstream csvfile;
  csvfile.open (filename);
  // sum up all lanes and report
  for (uint32_t ud = 0; ud < this->total_uds; ud++) {
    for (int ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
      uint32_t* instCounts_loc = uds[ud]->getInstCount(ln);
      for(uint32_t inst = 0; inst < static_cast<uint32_t>(basim::InstMap::COUNT); inst++){
        instCounts[inst] += instCounts_loc[inst];
      }
    }
  }
  for(uint32_t inst = 0; inst < static_cast<uint32_t>(basim::InstMap::COUNT); inst++){
    csvfile << InstNames[inst] << "," << instCounts[inst] << "\n";
  }
  csvfile.close();
}
#endif


void BASimUDRuntime_t::db_exec(std::string sql) {
  #if defined (ENABLE_SQLITE)
  char* errMsg = 0;
  int rc = sqlite3_exec(this->stats_db, sql.c_str(), 0, 0, &errMsg);
  if (rc != SQLITE_OK) {
    std::string error = errMsg;
    sqlite3_exec(this->stats_db, "ROLLBACK;", 0, 0, &errMsg);
    sqlite3_free(errMsg);
    BASIM_ERROR("SQL error: %s (error code: %d)", error.c_str(), rc);
  }
  #else
    std::cerr << "ENABLE_SQLITE flag not set. Ignore exec database." << std::endl;
  #endif
}

int BASimUDRuntime_t::db_write_label(const char label[]) {
  #if defined (ENABLE_SQLITE)
    std::string table_name;
    std::string sql;
    
    // Create the labels table
    table_name = "labels";
    sql = "CREATE TABLE IF NOT EXISTS " + table_name + " ("
          "id INTEGER PRIMARY KEY AUTOINCREMENT, "
          "label TEXT NOT NULL UNIQUE, "
          "final_tick INTEGER, "
          "sim_ticks INTEGER"
          ");";
    db_exec(sql);

    // Insert the label into the labels table if it doesn't already exist
    sql = "INSERT OR IGNORE INTO " + table_name + " (label, final_tick, sim_ticks) VALUES ('" + std::string(label) + "', " + std::to_string(this->globalTick) + ", " + std::to_string(this->simTicks) + ");";
    db_exec(sql);
    

    // Update the final_tick and sim_ticks values if the label already exists
    sql = "UPDATE " + table_name + " SET final_tick = " + std::to_string(this->globalTick) + ", sim_ticks = " + std::to_string(this->simTicks) + " WHERE label = '" + std::string(label) + "';";
    db_exec(sql);

    // Get the ID of the label
    int label_id;
    sql = "SELECT id FROM " + table_name + " WHERE label = '" + std::string(label) + "';";
    char* errMsg = 0;
    int rc = sqlite3_exec(this->stats_db, sql.c_str(), [](void* data, int argc, char** argv, char** colName) -> int {
        *static_cast<int*>(data) = std::stoi(argv[0]);
        return 0;
    }, &label_id, &errMsg);
    if (rc != SQLITE_OK) {
      std::string error = errMsg;
      sqlite3_exec(this->stats_db, "ROLLBACK;", 0, 0, &errMsg);
      sqlite3_free(errMsg);
      BASIM_ERROR("SQL error: %s", error.c_str());
    }
    return label_id;
  #else
    std::cerr << "ENABLE_SQLITE flag not set. Ignore writing stats to database." << std::endl;
    return 0;
  #endif
}


void BASimUDRuntime_t::db_write_stats(uint32_t start_nwid, uint32_t num_lanes, const char label[]) {
#if defined (ENABLE_SQLITE)
  std::string table_name;
  std::string sql;

  db_exec("BEGIN TRANSACTION;");
  int label_id = db_write_label(label);

  // Create the stats table
  table_name = "stats";
  sql = "CREATE TABLE IF NOT EXISTS " + table_name + " ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "label_id INTEGER NOT NULL, "
        "nwid INTEGER NOT NULL,"
        "Cycles INTEGER, "
        "InstructionCount INTEGER, "
        "TransitionCount INTEGER, "
        "ThreadCount INTEGER, "
        "MaxThreadCount INTEGER, "
        "Cycles_gt128th INTEGER, "
        "AtomicInstructions INTEGER, "
        "BitWiseInstructions INTEGER, "
        "CtrlFlowInstructions INTEGER, "
        "DataMovInstructions INTEGER, "
        "EvInstructions INTEGER, "
        "FPArithInstructions INTEGER, "
        "HashInstructions INTEGER, "
        "IntArithInstructions INTEGER, "
        "IntCompInstructions INTEGER, "
        "MsgInstructions INTEGER, "
        "MsgInstructionsMem INTEGER, "
        "MsgInstructionsLane INTEGER, "
        "ThrdCtrlInstructions INTEGER, "
        "TranCtrlInstructions INTEGER, "
        "VectorInstructions INTEGER, "
        "BasicTransitions INTEGER, "
        "MajorityTransitions INTEGER, "
        "DefaultTransitions INTEGER, "
        "EpsilonTransitions INTEGER, "
        "CommonTransitions INTEGER, "
        "FlaggedTransitions INTEGER, "
        "RefillTransitions INTEGER, "
        "EventTransitions INTEGER, "
        "MaxInstCountPerEvent INTEGER, "
        "MaxInstCountPerTx INTEGER, "
        "MessagesNodeCount INTEGER, "
        "MessagesNodeBytes INTEGER, "
        "DRAMStoreNodeCount INTEGER, "
        "DRAMStoreNodeBytes INTEGER, "
        "DRAMLoadNodeCount INTEGER, "
        "DRAMLoadNodeBytes INTEGER, "
        "DRAMStoreAckNodeCount INTEGER, "
        "DRAMStoreAckNodeBytes INTEGER, "
        "DRAMLoadAckNodeCount INTEGER, "
        "DRAMLoadAckNodeBytes INTEGER, "
        "LMLoadBytes INTEGER, "
        "LMStoreBytes INTEGER, "
        "LMLoadCount INTEGER, "
        "LMStoreCount INTEGER, "
        "DRAMLoadBytes INTEGER, "
        "DRAMStoreBytes INTEGER, "
        "DRAMLoadCount INTEGER, "
        "DRAMStoreCount INTEGER, "
        "MessageBytes INTEGER, "
        "EventQLenMax INTEGER, "
        "OperandQueueLenMax INTEGER, "
        "FOREIGN KEY(label_id) REFERENCES labels(id)"
        ");";
  db_exec(sql);

  for (uint32_t nwid = start_nwid; nwid < start_nwid + num_lanes; nwid++) {
    auto lnstats = uds[nwid/64]->getLaneStats(nwid%64);

    // Construct the INSERT statement
    sql = "INSERT INTO " + table_name + " (label_id, nwid, Cycles, InstructionCount, TransitionCount, ThreadCount, MaxThreadCount, "
          " Cycles_gt128th, AtomicInstructions, BitWiseInstructions, CtrlFlowInstructions, DataMovInstructions, EvInstructions, "
          "FPArithInstructions, HashInstructions, IntArithInstructions, IntCompInstructions, MsgInstructions, "
          "MsgInstructionsMem, MsgInstructionsLane, ThrdCtrlInstructions, TranCtrlInstructions, VectorInstructions, "
          "BasicTransitions, MajorityTransitions, DefaultTransitions, EpsilonTransitions, CommonTransitions, "
          "FlaggedTransitions, RefillTransitions, EventTransitions, "
          "MaxInstCountPerEvent, MaxInstCountPerTx, "
          "MessagesNodeCount, MessagesNodeBytes, "
          "DRAMStoreNodeCount, DRAMStoreNodeBytes, DRAMLoadNodeCount, DRAMLoadNodeBytes, "
          "DRAMStoreAckNodeCount, DRAMStoreAckNodeBytes, DRAMLoadAckNodeCount, DRAMLoadAckNodeBytes, "
          "LMLoadBytes, LMStoreBytes, LMLoadCount, LMStoreCount, DRAMLoadBytes, DRAMStoreBytes, DRAMLoadCount, "
          "DRAMStoreCount, MessageBytes, EventQLenMax, OperandQueueLenMax) VALUES ("
          + std::to_string(label_id) + ", " + std::to_string(nwid) + ", " +
          std::to_string(lnstats->cycle_count) + ", " +
          std::to_string(lnstats->inst_count) + ", " +
          std::to_string(lnstats->tran_count) + ", " +
          std::to_string(lnstats->thread_count) + ", " +
          std::to_string(lnstats->max_thread_count) + ", " +
          std::to_string(lnstats->cycles_gt128th) + ", " +
          std::to_string(lnstats->inst_count_atomic) + ", " +
          std::to_string(lnstats->inst_count_bitwise) + ", " +
          std::to_string(lnstats->inst_count_ctrlflow) + ", " +
          std::to_string(lnstats->inst_count_datmov) + ", " +
          std::to_string(lnstats->inst_count_ev) + ", " +
          std::to_string(lnstats->inst_count_fparith) + ", " +
          std::to_string(lnstats->inst_count_hash) + ", " +
          std::to_string(lnstats->inst_count_intarith) + ", " +
          std::to_string(lnstats->inst_count_intcmp) + ", " +
          std::to_string(lnstats->inst_count_msg) + ", " +
          std::to_string(lnstats->inst_count_msg_mem) + ", " +
          std::to_string(lnstats->inst_count_msg_lane) + ", " +
          std::to_string(lnstats->inst_count_threadctrl) + ", " +
          std::to_string(lnstats->inst_count_tranctrl) + ", " +
          std::to_string(lnstats->inst_count_vec) + ", " +
          std::to_string(lnstats->tran_count_basic) + ", " +
          std::to_string(lnstats->tran_count_majority) + ", " +
          std::to_string(lnstats->tran_count_default) + ", " +
          std::to_string(lnstats->tran_count_epsilon) + ", " +
          std::to_string(lnstats->tran_count_common) + ", " +
          std::to_string(lnstats->tran_count_flagged) + ", " +
          std::to_string(lnstats->tran_count_refill) + ", " +
          std::to_string(lnstats->tran_count_event) + ", " +
          #ifdef DETAIL_STATS
          std::to_string(lnstats->max_inst_per_event) + ", " +
          std::to_string(lnstats->max_inst_per_tx) + ", " +
          #else
          "NULL, NULL, " +
          #endif
          std::to_string(lnstats->tran_count_other_node) + ", " +
  		    std::to_string(lnstats->tran_bytes_other_node) + ", " +
  		    std::to_string(lnstats->dram_store_count_other_node) + ", " +
  		    std::to_string(lnstats->dram_store_bytes_other_node) + ", " +
  		    std::to_string(lnstats->dram_load_count_other_node) + ", " +
  		    std::to_string(lnstats->dram_load_bytes_other_node) + ", " +
          std::to_string(lnstats->dram_store_ack_count_other_node) + ", " +
  		    std::to_string(lnstats->dram_store_ack_bytes_other_node) + ", " +
  		    std::to_string(lnstats->dram_load_ack_count_other_node) + ", " +
  		    std::to_string(lnstats->dram_load_ack_bytes_other_node) + ", " +
          std::to_string(lnstats->lm_load_bytes) + ", " +
          std::to_string(lnstats->lm_store_bytes) + ", " +
          std::to_string(lnstats->lm_load_count) + ", " +
          std::to_string(lnstats->lm_store_count) + ", " +
          std::to_string(lnstats->dram_load_bytes) + ", " +
          std::to_string(lnstats->dram_store_bytes) + ", " +
          std::to_string(lnstats->dram_load_count) + ", " +
          std::to_string(lnstats->dram_store_count) + ", " +
          std::to_string(lnstats->message_bytes) + ", " +
          std::to_string(lnstats->eventq_len_max) + ", " +
          std::to_string(lnstats->opbuff_len_max) + ");";

    db_exec(sql);
  }

  // Commit transaction
  db_exec("COMMIT;");
  int rc = sqlite3_wal_checkpoint(this->stats_db, NULL);
  if (rc != SQLITE_OK) {
      std::cerr << "Checkpoint failed: " << sqlite3_errmsg(this->stats_db) << std::endl;
  }
#else
  std::cerr << "ENABLE_SQLITE flag not set. Ignore writing stats to database." << std::endl;
#endif
}

void BASimUDRuntime_t::print_histograms(uint32_t ud_id, uint8_t lane_num) {
  #ifdef DETAIL_STATS
  const basim::LaneStats* lnstats = uds[ud_id]->getLaneStats(lane_num);
  printf("[UD%d-L%d] Inst_Per_Event_Histogram   =[",ud_id, lane_num);
  uint64_t loc_count;
  for(int i = 0; i < MAX_BINS/BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * BUCKET_SIZE; j < (i + 1)*BUCKET_SIZE; j++)
      loc_count += lnstats->inst_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] LM_Count_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_COUNT_BINS/COUNT_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * COUNT_BUCKET_SIZE; j < (i + 1)*COUNT_BUCKET_SIZE; j++)
      loc_count += lnstats->lm_load_count_per_event[j] + lnstats->lm_store_count_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*COUNT_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] LM_Bytes_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_BYTES_BINS/BYTES_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * BYTES_BUCKET_SIZE; j < (i + 1)*BYTES_BUCKET_SIZE; j++)
      loc_count += lnstats->lm_load_bytes_per_event[j] + lnstats->lm_store_bytes_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*BYTES_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] DRAM_Count_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_COUNT_BINS/COUNT_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * COUNT_BUCKET_SIZE; j < (i + 1)*COUNT_BUCKET_SIZE; j++)
      loc_count += lnstats->dram_load_count_per_event[j] + lnstats->dram_store_count_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*COUNT_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] DRAM_Bytes_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_BYTES_BINS/BYTES_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * BYTES_BUCKET_SIZE; j < (i + 1)*BYTES_BUCKET_SIZE; j++)
      loc_count += lnstats->dram_load_bytes_per_event[j] + lnstats->dram_store_bytes_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*BYTES_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  #else
    std::cerr << "DETAIL_STATS flag not set. Ignore printing statistics." << std::endl;
  #endif
}

void BASimUDRuntime_t::print_histograms(uint32_t nwid) {
  print_histograms(nwid/64, nwid%64);
}

/**
  * Print the event stats for a given network id
  * Each line:
  * NWID,EventName,EventCycleCount,EventActivationCount,EventAvgCycleCount
  */
void BASimUDRuntime_t::print_event_stats(uint32_t nwid) {
  #ifdef DETAIL_STATS
  auto lnstats = uds[nwid/64]->getLaneStats(nwid%64);
  auto sym_map = uds[nwid/64]->getSymbolNameMap();
  for (auto &sym : lnstats->event_cycle_count) {
    if (sym.second == 0) {
      continue;
    }
    uint64_t cycle_count = sym.second;
    uint64_t activation_count = lnstats->event_activation_count.at(sym.first);
    uint64_t avg_cycle_count = static_cast<uint64_t>((static_cast<long double>(sym.second) / lnstats->event_activation_count.at(sym.first)));
    printf("%u,%s,%lu,%lu,%lu\n", nwid, sym_map[sym.first].c_str(), cycle_count, activation_count, avg_cycle_count);
  }
  #else
    std::cerr << "DETAIL_STATS flag not set. Ignore printing statistics." << std::endl;
  #endif
}

/**
  * Print the event stats for a given UD and lane
  * Each line:
  * NWID,EventName,EventCycleCount,EventActivationCount,EventAvgCycleCount
  */
void BASimUDRuntime_t::print_event_stats(uint32_t ud_id, uint8_t lane_num) {
  #ifdef DETAIL_STATS
  auto lnstats = uds[ud_id]->getLaneStats(lane_num);
  auto sym_map = uds[ud_id]->getSymbolNameMap();
  for (auto &sym : lnstats->event_cycle_count) {
    if (sym.second == 0) {
      continue;
    }
    uint64_t cycle_count = sym.second;
    uint64_t activation_count = lnstats->event_activation_count.at(sym.first);
    uint64_t avg_cycle_count = static_cast<uint64_t>((static_cast<long double>(sym.second) / lnstats->event_activation_count.at(sym.first)));
    printf("%u,%u,%s,%lu,%lu,%lu\n", ud_id, lane_num, sym_map[sym.first].c_str(), cycle_count, activation_count, avg_cycle_count);
  }
  #else
    std::cerr << "DETAIL_STATS flag not set. Ignore printing statistics." << std::endl;
  #endif
}

void BASimUDRuntime_t::db_write_event_stats(uint32_t start_nwid, uint32_t num_lanes, const char label[]) {
#if defined (ENABLE_SQLITE) && defined(DETAIL_STATS)
  std::string table_name;
  std::string sql;

  // Begin transaction
  db_exec("BEGIN TRANSACTION;");
  int label_id = db_write_label(label);

  // Create the events table
  table_name = "events";
  sql = "CREATE TABLE IF NOT EXISTS " + table_name + " ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "event_name TEXT NOT NULL UNIQUE"
        ");";
  db_exec(sql);

  // Get the symbol name map and insert all event names into the events table
  auto sym_map = uds[start_nwid/64]->getSymbolNameMap();
  for (const auto &sym : sym_map) {
    sql = "INSERT OR IGNORE INTO events (event_name) VALUES ('" + sym.second + "');";
    db_exec(sql);
  }

  // Create the event_stats table
  table_name = "event_stats";
  sql = "CREATE TABLE IF NOT EXISTS " + table_name + " ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "label_id INTEGER NOT NULL, "
        "nwid INTEGER NOT NULL, "
        "event_name_id INTEGER NOT NULL, "
        "cycle_count INTEGER, "
        "activation_count INTEGER, "
        "avg_cycle_count INTEGER, "
        "FOREIGN KEY(label_id) REFERENCES labels(id), "
        "FOREIGN KEY(event_name_id) REFERENCES events(id)"
        ");";
  db_exec(sql);

  for (uint32_t nwid = start_nwid; nwid < start_nwid + num_lanes; nwid++) {
    auto lnstats = uds[nwid/64]->getLaneStats(nwid%64);
    for (auto &sym : lnstats->event_cycle_count) {
      if (sym.second == 0) {
        continue;
      }
      uint64_t cycle_count = sym.second;
      uint64_t activation_count = lnstats->event_activation_count.at(sym.first);
      uint64_t avg_cycle_count = static_cast<uint64_t>((static_cast<long double>(sym.second) / lnstats->event_activation_count.at(sym.first)));

      // Get the ID of the event_name
      int event_name_id;
      sql = "SELECT id FROM events WHERE event_name = '" + sym_map[sym.first] + "';";
      char *errMsg = 0;
      int rc = sqlite3_exec(this->stats_db, sql.c_str(), [](void* data, int argc, char** argv, char** colName) -> int {
          *static_cast<int*>(data) = std::stoi(argv[0]);
          return 0;
      }, &event_name_id, &errMsg);
      if (rc != SQLITE_OK) {
        std::string error = errMsg;
        sqlite3_exec(this->stats_db, "ROLLBACK;", 0, 0, &errMsg);
        sqlite3_free(errMsg);
        BASIM_ERROR("SQL error 12: %s", error.c_str());
      }

      // Construct the INSERT statement for event_stats
      sql = "INSERT INTO " + table_name + " (label_id, nwid, event_name_id, cycle_count, activation_count, avg_cycle_count) VALUES ("
            + std::to_string(label_id) + ", " + std::to_string(nwid) + ", " + std::to_string(event_name_id) + ", "
            + std::to_string(cycle_count) + ", "
            + std::to_string(activation_count) + ", "
            + std::to_string(avg_cycle_count) + ");";

      db_exec(sql);
    }
  }

  // Commit transaction
  db_exec("COMMIT;");
  int rc = sqlite3_wal_checkpoint(this->stats_db, NULL);
  if (rc != SQLITE_OK) {
      std::cerr << "Checkpoint failed: " << sqlite3_errmsg(this->stats_db) << std::endl;
  }
#else
  std::cerr << "ENABLE_SQLITE and DETAIL_STATS flags not set. Ignore writing event stats to database." << std::endl;
#endif
}


void BASimUDRuntime_t::db_write_node_stats(uint32_t start_node, uint32_t num_nodes, const char label[]) {
#if defined (ENABLE_SQLITE) && defined(DETAIL_STATS)
  std::string table_name;
  std::string sql;

  db_exec("BEGIN TRANSACTION;");
  std::string label_id = std::to_string(db_write_label(label));

  // Create the node_stats table
  table_name = "node_stats";
  sql = "CREATE TABLE IF NOT EXISTS " + table_name + " ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "label_id INTEGER NOT NULL, "
        "srcNode INTEGER NOT NULL, "
        "dstNode INTEGER, "
        "MessagesNodeCount INTEGER, "
        "MessagesNodeBytes INTEGER, "
        "DRAMStoreNodeCount INTEGER, "
        "DRAMStoreNodeBytes INTEGER, "
        "DRAMLoadNodeCount INTEGER, "
        "DRAMLoadNodeBytes INTEGER, "
        "DRAMStoreAckNodeCount INTEGER, "
        "DRAMStoreAckNodeBytes INTEGER, "
        "DRAMLoadAckNodeCount INTEGER, "
        "DRAMLoadAckNodeBytes INTEGER, "
        "FOREIGN KEY(label_id) REFERENCES labels(id)"
        ");";
  db_exec(sql);

  #if defined(NETWORK_STATS)
  for (uint32_t nodeID = start_node; nodeID < num_nodes; ++nodeID) {
    #ifdef ASST_FASTSIM
      uint32_t upperLimit = 1;
    #else
      uint32_t upperLimit = this->MachineConfig.NumNodes;
    #endif

    for(uint32_t dstNodeID=0; dstNodeID<upperLimit; ++dstNodeID) {
      if(dstNodeID == nodeID) {
        continue;
      }
      
      // Construct the INSERT statement for event_stats
      sql = "INSERT INTO " + table_name + " (label_id, srcNode, dstNode, MessagesNodeCount, MessagesNodeBytes, DRAMStoreNodeCount, DRAMStoreNodeBytes, DRAMLoadNodeCount, DRAMLoadNodeBytes, DRAMStoreAckNodeCount, DRAMStoreAckNodeBytes, DRAMLoadAckNodeCount, DRAMLoadAckNodeBytes)) VALUES ("
            + label_id + ", " + std::to_string(nodeID) + ", " + std::to_string(dstNodeID) + ", "
            + std::to_string(this->simNodeStats[nodeID].tran_count_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].tran_bytes_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_store_count_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_store_bytes_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_load_count_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_load_bytes_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_store_ack_count_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_store_ack_bytes_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_load_ack_count_other_node[dstNodeID]->load()) + ", "
            + std::to_string(this->simNodeStats[nodeID].dram_load_ack_bytes_other_node[dstNodeID]->load()) + ");";

      db_exec(sql);
    }
  }
    #endif


  // Adding per stack stats for each node
  table_name = "node_stack_stats";
  sql = "CREATE TABLE IF NOT EXISTS " + table_name + " ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "label_id INTEGER NOT NULL, "
        "node INTEGER NOT NULL, ";
  for(int stid = 0; stid < this->MachineConfig.NumStacks; stid++){
    sql += "DRAMStoreCountStack" + std::to_string(stid) + " INTEGER, "
        "DRAMStoreBytesStack" + std::to_string(stid) + " INTEGER, "
        "DRAMLoadCountStack" + std::to_string(stid) + " INTEGER, "
        "DRAMLoadBytesStack" + std::to_string(stid) + " INTEGER, ";
  }
  sql += "FOREIGN KEY(label_id) REFERENCES labels(id)"
      ");";
  db_exec(sql);

  for (uint32_t nodeID = start_node; nodeID < num_nodes; ++nodeID) {
      // Construct the INSERT statement for event_stats
      sql = "INSERT INTO " + table_name + " (label_id, node";
      for(int stid = 0; stid < this->MachineConfig.NumStacks; stid++){
        sql += ", DRAMStoreCountStack" + std::to_string(stid) + 
            ", DRAMStoreBytesStack" + std::to_string(stid) + 
            ", DRAMLoadCountStack" + std::to_string(stid) + 
            ", DRAMLoadBytesStack" + std::to_string(stid);
      }
      sql += ") VALUES("
            + label_id + ", " + std::to_string(nodeID);
      for(int stid = 0; stid < this->MachineConfig.NumStacks; stid++){
        const basim::StackStats* ststats = udMems[nodeID]->getStackStats(stid);
        sql += ", " + std::to_string(ststats->dram_store_count)
            + ", " + std::to_string(ststats->dram_store_bytes)
            + ", " + std::to_string(ststats->dram_load_count)
            + ", " + std::to_string(ststats->dram_load_bytes);
      }
      sql += ");";
      db_exec(sql);
  }

  // Commit transaction
  db_exec("COMMIT;");
  int rc = sqlite3_wal_checkpoint(this->stats_db, NULL);
  if(rc != SQLITE_OK) {
      std::cerr << "Checkpoint failed: " << sqlite3_errmsg(this->stats_db) << std::endl;
  }
#else
  std::cerr << "ENABLE_SQLITE and DETAIL_STATS flags not set. Ignore writing event stats to database." << std::endl;
#endif
}


BASimUDRuntime_t::~BASimUDRuntime_t() {
  // close perflog
  basim::globalLogs.perflog.close();
  // close tracelog
  basim::globalLogs.tracelog.close();
#if defined (ENABLE_SQLITE)
  // close db
  sqlite3_close(this->stats_db);
#endif

  // Delete the uds
  for (auto &ud : uds) {
    delete ud;
  }
  uds.clear();
}

bool BASimUDRuntime_t::isIdle(uint32_t udid, uint32_t laneID){
  return uds[udid]->isIdle(laneID);
}

void BASimUDRuntime_t::simulate(uint32_t udid, uint32_t laneID, uint64_t numTicks, uint64_t timestamp){
  uds[udid]->simulate(laneID, NumTicks, timestamp);
}


common_addr BASimUDRuntime_t::mapSA2PA(basim::Addr mm_addr, uint8_t isGlobal){
    common_addr final_addr;
    final_addr.isGlobal = isGlobal;
    final_addr.addr = 0;
    final_addr.node_id = -1;
#ifdef ASST_FASTSIM
    // local memory
    if(isGlobal == 0){
        final_addr.addr = mm_addr;
        final_addr.node_id = nodeID;
    }
    else if(isGlobal == 1){ // global memory
        final_addr.node_id = nodeID;
        basim::Addr offset = mm_addr - this->MachineConfig.PhysGMapMemBase;
        final_addr.addr = (nodeID << 37) | offset;
    }
#else
    // local memory
    if(isGlobal == 0){
        final_addr.node_id = 0;
        final_addr.addr = mm_addr;
    }
    else if(isGlobal == 1){ // global memory
        uint64_t memSize = this->MachineConfig.GMapMemSize / this->MachineConfig.NumNodes;
        basim::Addr offset = mm_addr - this->MachineConfig.PhysGMapMemBase;
        uint64_t node_id = offset / memSize;
        offset = offset % memSize;
        final_addr.addr = (node_id << 37) | offset;
        final_addr.node_id = node_id;
    }
#endif
    return final_addr;
}

common_addr BASimUDRuntime_t::mapPA2SA(basim::Addr ud_addr, uint8_t isGlobal){
    common_addr final_addr;
    final_addr.isGlobal = isGlobal;
    final_addr.addr = 0;
    final_addr.node_id = -1;
    #ifdef ASST_FASTSIM
        // local memory
        if(isGlobal == 0){
            final_addr.node_id = nodeID;
            final_addr.addr = ud_addr;
        }
        // global memory
        else if(isGlobal == 1)
        {
            uint64_t node_id = (ud_addr >> 37) & 0x3FFFULL;
            basim::Addr Offset = ud_addr & 0xF'FFFF'FFFFULL;
            final_addr.node_id = node_id;
            final_addr.addr = this->MachineConfig.PhysGMapMemBase + Offset;
        }
    #else
        // local memory
        if(isGlobal == 0){
            final_addr.node_id = 0;
            final_addr.addr = ud_addr;
        }
        // global memory
        else if(isGlobal == 1)
        {
            uint64_t node_id = (ud_addr >> 37) & 0x3FFFULL;
            basim::Addr offset = ud_addr & 0x1f'ffff'fffful;
            final_addr.node_id = node_id;

            uint64_t memPerNode = this->MachineConfig.GMapMemSize / this->MachineConfig.NumNodes;
            final_addr.addr = this->MachineConfig.PhysGMapMemBase + (memPerNode * node_id) + offset;
            
            // printf("mapPA2SA: udpa_addr = 0x%lx, isGlobal = %d, node_id = %ld, memPerNode = 0x%lx, offset = 0x%lx, simulator_addr = 0x%lx\n", 
            //               ud_addr, isGlobal, node_id, memPerNode, offset, final_addr.addr);
        }
    #endif
    return final_addr;
} 

uint64_t BASimUDRuntime_t::get_status(){
    return status.load(std::memory_order_relaxed);
}
void BASimUDRuntime_t::set_status(uint64_t _status){
    status.store(_status, std::memory_order_release);
}


uint64_t BASimUDRuntime_t::get_barrier_times(){
    return barrier_times_atomic.load(std::memory_order_relaxed);
}
void BASimUDRuntime_t::set_barrier_times(uint64_t _barrier_times){
    barrier_times_atomic.store(_barrier_times, std::memory_order_release);
}

void BASimUDRuntime_t::barrier(uint64_t barrier_id){
#ifdef ASST_FASTSIM
    pthread_mutex_lock(&map_lock);
    pthread_t tid = pthread_self();
    int id1 = 0;
    auto it1 = thread_map.find(tid);
    if (it1 != thread_map.end()) {
        id1 = it1->second;
    }else{
        id1 = thread_num.load(std::memory_order_relaxed);
        thread_num.store(id1+1, std::memory_order_release);
        thread_map[tid] = id1;
    }
    pthread_mutex_unlock(&map_lock);
    while(get_status() != 0){
        fflush(stdout);
    }
    set_status(10+id1);
    sem_wait(&semSync[id1]);
#else
   uint64_t barrier_times = get_barrier_times();
    while(get_status() != barrier_id){
        fflush(stdout);
    }
    set_status(barrier_id+1);
    if(get_status() == (barrier_times)){
        set_status(barrier_times - 1);
    }
    while(get_status() != barrier_id){
        fflush(stdout);
    }
    if(barrier_id > 0)
        set_status(barrier_id-1);
#endif
}

void BASimUDRuntime_t::barrier(){
#ifdef ASST_FASTSIM
    pthread_mutex_lock(&map_lock);
    pthread_t tid = pthread_self();
    int id1 = 0;
    auto it1 = thread_map.find(tid);
    if (it1 != thread_map.end()) {
        id1 = it1->second;
    }else{
        id1 = thread_num.load(std::memory_order_relaxed);
        thread_num.store(id1+1, std::memory_order_release);
        thread_map[tid] = id1;
    }
    pthread_mutex_unlock(&map_lock);
    while(get_status() != 0){
        fflush(stdout);
    }
    set_status(10+id1);
    sem_wait(&semSync[id1]);
#else
    uint64_t barrier_id = nodeID;
    uint64_t barrier_times = get_barrier_times();
    while(get_status() != barrier_id){
        fflush(stdout);
    }
    set_status(barrier_id+1);
    if(get_status() == (barrier_times)){
        set_status(barrier_times - 1);
    }
    while(get_status() != barrier_id){
        fflush(stdout);
    }
    if(barrier_id > 0)
        set_status(barrier_id-1);
#endif
}

void BASimUDRuntime_t::lock(){
    pthread_mutex_lock(&top_lock);
}

void BASimUDRuntime_t::unlock(){
    pthread_mutex_unlock(&top_lock);
}

void BASimUDRuntime_t::reorder_freetids(){
    for (int ud = 0; ud < total_uds; ud++)
        this->uds[ud]->reorder_freetids();
}


} // namespace UpDown
