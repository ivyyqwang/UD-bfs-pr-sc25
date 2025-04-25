#include "updown.h"
#include <cstdio>
#include <cstdlib>
#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif
namespace UpDown {

// TODO: This should not be offset with the number of elements. Best to
// determine a fixed memory location for each section

  UDRuntime_t::UDRuntime_t() {
    UPDOWN_INFOMSG("Initializing runtime");
    calc_addrmap();
    MappedMemoryManager = new ud_mapped_memory_t(this->MachineConfig);
    #ifdef GEM5_MODE
    uint64_t* sync1 = (uint64_t*)BASE_SYNC_SPACE;
    sync1[0] = 0;
    sync1[1] = 0;
    this->nnodes = this->MachineConfig.NumNodes;
    this->nodeID = 0;
    this->topPerNode = 1;
    barrier_times = this->nnodes;
    #endif
  }

  UDRuntime_t::UDRuntime_t(ud_machine_t machineConfig) : MachineConfig(machineConfig) {
    // printf("nnodes = %llu\n", this->MachineConfig.NumNodes);
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    calc_addrmap();
    MappedMemoryManager = new ud_mapped_memory_t(this->MachineConfig);
    // printf("nnodes = %llu\n", this->MachineConfig.NumNodes);
    #ifdef GEM5_MODE
    uint64_t* sync1 = (uint64_t*)BASE_SYNC_SPACE;
    sync1[0] = 0;
    sync1[1] = 0;
    this->nnodes = this->MachineConfig.NumNodes;
    this->nodeID = 0;
    this->topPerNode = 1;
    barrier_times = this->nnodes;
    #endif
  }

    UDRuntime_t::UDRuntime_t(ud_machine_t machineConfig, uint64_t nodeID, uint64_t topPerNode) : MachineConfig(machineConfig), topPerNode(topPerNode), nodeID(nodeID){
    // printf("nnodes = %llu\n", this->MachineConfig.NumNodes);
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    calc_addrmap();
    MappedMemoryManager = new ud_mapped_memory_t(this->MachineConfig);
    // printf("nnodes = %llu\n", this->MachineConfig.NumNodes);
    #ifdef GEM5_MODE
    uint64_t* sync1 = (uint64_t*)BASE_SYNC_SPACE;
    sync1[0] = 0;
    sync1[1] = 0;
    this->nnodes = this->MachineConfig.NumNodes;
    barrier_times = this->nnodes;
    #endif
  }

void UDRuntime_t::set_barrier_times(uint64_t _barrier_times){
    barrier_times = _barrier_times;
}

uint64_t UDRuntime_t::get_barrier_times(){
    return barrier_times;
}

void UDRuntime_t::reorder_freetids(){
    // TODO need to call uds[i]->reorder_freetids()
}
    

void UDRuntime_t::barrier(){
    #ifdef GEM5_MODE
    uint64_t barreir_id = nodeID;
    // printf("wait on barrier id %llu\n", barreir_id);
    // fflush(stdout);
    uint64_t* sync1 = (uint64_t*)BASE_SYNC_SPACE;
    while(sync1[0] != barreir_id){
        // printf("sync = %lu\n", sync1[0]);
        fflush(stdout);
    }
    __sync_fetch_and_add(&sync1[0], 1);
    // printf("sync = %lu node %lu\n", sync1[0], nodeID);
    if(sync1[0] == (barrier_times)){
        sync1[0] = barrier_times - 1;
        // printf("finish sync reset\n");
    }
    // printf("sync = %lu node %lu %lu\n", sync1[0], nodeID, (MachineConfig.NumNodes));
    while(sync1[0] != barreir_id){
        fflush(stdout);
    }
    if(barreir_id > 0)
        __sync_fetch_and_sub(&sync1[0], 1);
//    printf("pass barreir id %llu\n", barreir_id);
   #endif
}

void UDRuntime_t::barrier(uint64_t barreir_id){
    #ifdef GEM5_MODE
    // printf("wait on barrier id %llu\n", barreir_id);
    // fflush(stdout);
    uint64_t* sync1 = (uint64_t*)BASE_SYNC_SPACE;
    while(sync1[0] != barreir_id){
        // printf("sync = %lu\n", sync1[0]);
        fflush(stdout);
    }
    __sync_fetch_and_add(&sync1[0], 1);
    // printf("sync = %lu node %lu\n", sync1[0], nodeID);
    if(sync1[0] == (barrier_times)){
        sync1[0] = barrier_times - 1;
        // printf("finish sync reset\n");
    }
    // printf("sync = %lu node %lu %lu\n", sync1[0], nodeID, (MachineConfig.NumNodes));
    while(sync1[0] != barreir_id){
        fflush(stdout);
    }
    if(barreir_id > 0)
        __sync_fetch_and_sub(&sync1[0], 1);
//    printf("pass barreir id %llu\n", barreir_id);
   #endif


    // uint64_t value = __sync_fetch_and_add(&sync1[1], 0);
    // while(value != 0){
    //     value = __sync_fetch_and_add(&sync1[1], 0);
    // }
    // uint64_t v0 = __sync_fetch_and_add(&sync1[0], 1);
    // while(v0 != MachineConfig.NumNodes){
    //     printf("sync = %lu\n", v0);
    //     fflush(stdout);
    //     v0 = __sync_fetch_and_add(&sync1[0], 0);
    // }
    // printf("finish sync\n");
    // fflush(stdout);
    // value = __sync_fetch_and_add(&sync1[1], 1);
    // if(value == (MachineConfig.NumNodes-1)){
    //     sync1[0] = 0;
    //     sync1[1] = 0;
    //     printf("finish sync reset\n");
    //     fflush(stdout);
    // }
  }

void UDRuntime_t::calc_addrmap() {
  BaseAddrs.mmaddr = (ptr_t)MachineConfig.MapMemBase;
  BaseAddrs.spaddr = (ptr_t)MachineConfig.SPMemBase;
  BaseAddrs.ctrlAddr = (ptr_t)MachineConfig.ControlBase;
  BaseAddrs.progAddr = (ptr_t)MachineConfig.ProgBase;
  UPDOWN_INFOMSG("calc_addrmap: maddr: 0x%lX spaddr: 0x%lX ctrlAddr: 0x%lX", reinterpret_cast<uint64_t>(BaseAddrs.mmaddr),
                 reinterpret_cast<uint64_t>(BaseAddrs.spaddr), reinterpret_cast<uint64_t>(BaseAddrs.ctrlAddr), reinterpret_cast<uint64_t>(BaseAddrs.progAddr));
}

void UDRuntime_t::send_event(event_t ev) {
  uint64_t offset = (((ev.get_NetworkId()).get_NodeId() * MachineConfig.CapNumStacks + (ev.get_NetworkId()).get_StackId()) * MachineConfig.CapNumUDs +
                     (ev.get_NetworkId()).get_UdId()) *
                        MachineConfig.CapNumLanes * MachineConfig.CapControlPerLane +
                    (ev.get_NetworkId()).get_LaneId() * MachineConfig.CapControlPerLane;
  // Convert from bytes to words. the pointers are ptr_t
  offset /= sizeof(word_t);
  // Locking the lane's queues
  auto lock = (BaseAddrs.ctrlAddr + offset + MachineConfig.LockOffset);
  UPDOWN_INFOMSG("Locking 0x%lX", reinterpret_cast<uint64_t>(lock));
  *lock = 1;
  // Set the event Queue

  // TODO: Num Operands should reflect the continuation, this should not be a +
  // 1 in the for
  auto OpsQ = (BaseAddrs.ctrlAddr + offset + MachineConfig.OperandQueueOffset);
  UPDOWN_INFOMSG("Using Operands Queue 0x%lX", reinterpret_cast<uint64_t>(OpsQ));
  if (ev.get_NumOperands() != 0)
    for (uint8_t i = 0; i < ev.get_NumOperands() + 1; i++) {
      *(OpsQ) = ev.get_OperandsData()[i];
      UPDOWN_INFOMSG("OB[%u]: %lu (0x%lX)", i, ev.get_OperandsData()[i], ev.get_OperandsData()[i]);
    }
  UPDOWN_INFOMSG("Unlocking 0x%lX", reinterpret_cast<uint64_t>(lock));
  auto eventQ = (BaseAddrs.ctrlAddr + offset + MachineConfig.EventQueueOffset);
  UPDOWN_INFOMSG("Sending Event:%u to [%u, %u, %u, %u, %u] to queue at 0x%lX", ev.get_EventLabel(), ev.get_NetworkId().get_NodeId(),
                 ev.get_NetworkId().get_StackId(), ev.get_NetworkId().get_UdId(), ev.get_NetworkId().get_LaneId(), ev.get_ThreadId(),
                 reinterpret_cast<uint64_t>(eventQ));
  *eventQ = ev.get_EventWord();
  *(lock) = 0;

  // Set the Operand Queue
}

void UDRuntime_t::start_exec(networkid_t nwid) {
  uint8_t ud_id = nwid.get_UdId();
  uint8_t lane_id = nwid.get_LaneId();
  uint8_t stack_id = nwid.get_StackId();
  uint16_t node_id = nwid.get_NodeId();
  uint64_t offset = (node_id * MachineConfig.CapNumStacks * MachineConfig.CapNumUDs + stack_id * MachineConfig.CapNumUDs + ud_id) * MachineConfig.CapNumLanes *
                        MachineConfig.CapControlPerLane +
                    lane_id * MachineConfig.CapControlPerLane;
  // Convert from bytes to words. the pointers are ptr_t
  offset /= sizeof(word_t);
  auto startSig = BaseAddrs.ctrlAddr + offset + MachineConfig.StartExecOffset;
  *(startSig) = 1;
  UPDOWN_INFOMSG("Starting execution UD %u, Lane %u. Signal in  0x%lX", ud_id, lane_id, reinterpret_cast<uint64_t>(startSig));
}

uint32_t UDRuntime_t::get_globalUDNum(networkid_t &nid) {
#ifdef ASST_FASTSIM
    return nid.get_StackId() * (this->MachineConfig.NumUDs) + nid.get_UdId();
#else
    return nid.get_NodeId() * (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs) + nid.get_StackId() * (this->MachineConfig.NumUDs) + nid.get_UdId();
#endif
}

uint64_t UDRuntime_t::get_lane_aligned_offset(networkid_t nwid, uint32_t offset) {
  auto alignment = sizeof(word_t);
  auto aligned_offset = offset - offset % alignment;
  uint8_t ud_id = nwid.get_UdId();
  uint8_t lane_id = nwid.get_LaneId();
  uint8_t stack_id = nwid.get_StackId();
  uint16_t node_id = nwid.get_NodeId();
  UPDOWN_WARNING_IF(offset % alignment != 0, "Unaligned offset %u", offset);
  uint64_t returned_offset = (node_id * MachineConfig.CapNumStacks * MachineConfig.CapNumUDs + stack_id * MachineConfig.CapNumUDs + ud_id) *
                                 MachineConfig.CapNumLanes * MachineConfig.CapSPmemPerLane +
                             MachineConfig.CapSPmemPerLane * lane_id + // Lane offset
                             aligned_offset;
  return returned_offset;
}

uint64_t UDRuntime_t::get_lane_physical_memory(networkid_t nwid, uint32_t offset) {
  uint8_t ud_id = nwid.get_UdId();
  uint8_t lane_id = nwid.get_LaneId();
  uint8_t stack_id = nwid.get_StackId();
  uint16_t node_id = nwid.get_NodeId();
  auto alignment = sizeof(word_t);
  auto aligned_offset = offset - offset % alignment;
  UPDOWN_WARNING_IF(offset % alignment != 0, "Unaligned offset %u", offset);
  uint64_t returned_offset =
      ((node_id * MachineConfig.NumStacks + stack_id) * MachineConfig.NumUDs + ud_id) * MachineConfig.NumLanes * MachineConfig.SPBankSize +
      lane_id * MachineConfig.SPBankSize + // Lane offset
      aligned_offset + MachineConfig.SPMemBase;
  return returned_offset;
}

uint64_t UDRuntime_t::get_ud_physical_memory(networkid_t nwid) {
  uint8_t ud_id = nwid.get_UdId();
  uint8_t stack_id = nwid.get_StackId();
  uint16_t node_id = nwid.get_NodeId();
  uint64_t returned_offset =
      ((node_id * MachineConfig.NumStacks + stack_id) * MachineConfig.NumUDs + ud_id) * MachineConfig.NumLanes * MachineConfig.SPBankSize +
      MachineConfig.SPMemBase;
  return returned_offset;
}

void UDRuntime_t::dumpMemory(const char* filename, void* vaddr, uint64_t size){
#ifdef GEM5_MODE
  m5_dump_mem(vaddr, size, filename);
#endif
}

std::pair<void *, uint64_t> UDRuntime_t::loadMemory(const char* filename, void* vaddr, uint64_t size) {
  size_t loadedBytes; // just to prevent compiler warnings
#ifdef GEM5_MODE
  FILE* mem_file = fopen(filename, "rb");
  UPDOWN_ERROR_IF(!mem_file, "Could not open %s", filename)

  fseek(mem_file, 0, SEEK_SET);
  // Read 'F' to indicate dump by Fastsim
  char dump_type;
  loadedBytes = fread(&dump_type, sizeof(char), 1, mem_file);
  UPDOWN_ERROR_IF(dump_type != 'G', "DRAM dump load failed! Not a Gem5 dump file!\n");
  // Read 'D' to indicate DRAM dump
  loadedBytes = fread(&dump_type, sizeof(char), 1, mem_file);
  UPDOWN_ERROR_IF(dump_type != 'D', "DRAM dump load failed! Not a DRAM dump file!\n");
  // Read dump start file offset
  uint64_t dump_start_file_offset;
  loadedBytes = fread(&dump_start_file_offset, sizeof(uint64_t), 1, mem_file);
  UPDOWN_INFOMSG("DRAM Dump start file offset: %lu", dump_start_file_offset);
  // Read dump vaddr
  uint64_t dump_vaddr;
  loadedBytes = fread(&dump_vaddr, sizeof(uint64_t), 1, mem_file);
  if (vaddr == nullptr) {
    vaddr = reinterpret_cast<void *>(dump_vaddr);
    UPDOWN_INFOMSG("DRAM Dump vaddr (from dump file): %p", vaddr);
  } else {
    UPDOWN_INFOMSG("DRAM Dump vaddr (user specified): %p", vaddr);
  }
  // Read dump size
  uint64_t dump_size;
  loadedBytes = fread(&dump_size, sizeof(uint64_t), 1, mem_file);
  if (vaddr == nullptr || size == 0) {
    size = dump_size;
    UPDOWN_INFOMSG("DRAM Dump size (from dump file): %lu", size);
  } else {
    UPDOWN_INFOMSG("DRAM Dump size (user specified): %lu", size);
  }
  fclose(mem_file);

  if (this->mm_malloc_global_at_addr(vaddr, size) == nullptr && this->mm_malloc_at_addr(vaddr, size) == nullptr) { // allocate memory
    UPDOWN_ERROR("DRAM dump load failed! Cannot allocate memory at (%p, %lu)", vaddr, size);
  }

  m5_load_mem(vaddr, size, filename);
  // m5_load_mem(0, 0, filename);

  return std::make_pair(vaddr, size);
#else
  return std::make_pair(nullptr, 0);
#endif
}

size_t UDRuntime_t::dumpMemoryTranslation(std::string filename, uint64_t nodeID) {
  // Alex TODO
  return 0;
}

size_t UDRuntime_t::loadMemoryTranslation(std::string filename, uint64_t nodeID, void* dumpVA) {
  // Alex TODO
  return 0;
}

void UDRuntime_t::dumpLocalMemory(const char* filename, networkid_t start_nwid, uint64_t num_lanes) {
#ifdef GEM5_MODE
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    num_lanes = this->MachineConfig.NumLanes * this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes;
  }
  m5_dump_udlm(BaseAddrs.spaddr, start_nwid.get_NetworkId_UdName(), num_lanes, filename);
#endif
}

std::pair<networkid_t, uint64_t> UDRuntime_t::loadLocalMemory(const char* filename, networkid_t start_nwid, uint64_t num_lanes){
#if defined(GEM5_MODE)
  size_t loadedBytes;
  FILE* spd_file = fopen(filename, "rb");
  UPDOWN_ERROR_IF(!spd_file, "Could not open %s", filename)

  fseek(spd_file, 0, SEEK_SET);
  // Read 'F' to indicate dump by Fastsim
  char dump_type;
  loadedBytes = fread(&dump_type, sizeof(char), 1, spd_file);
  UPDOWN_ERROR_IF(dump_type != 'G', "DRAM dump load failed! Not a Gem5 dump file!\n");
  // Read 'L' to indicate LM dump
  loadedBytes = fread(&dump_type, sizeof(char), 1, spd_file);
  UPDOWN_ERROR_IF(dump_type != 'L', "DRAM dump load failed! Not a LM dump file!\n");
  // Read dump start file offset
  uint64_t dump_start_file_offset;
  loadedBytes = fread(&dump_start_file_offset, sizeof(uint64_t), 1, spd_file);
  UPDOWN_INFOMSG("LM Dump start file offset: %lu", dump_start_file_offset);
  // Read dump start nwid (ud_name only)
  uint64_t dump_start_nwid_raw;
  loadedBytes = fread(&dump_start_nwid_raw, sizeof(uint64_t), 1, spd_file);
  networkid_t dump_start_nwid(dump_start_nwid_raw, false, 0);
  UPDOWN_INFOMSG("LM Dump start nwid (from dump file): %lu", dump_start_nwid_raw);
  // Read num lanes dumped
  uint64_t dump_num_lanes;
  loadedBytes = fread(&dump_num_lanes, sizeof(uint64_t), 1, spd_file);
  UPDOWN_INFOMSG("LM Dump num lanes (from dump file): %lu", dump_num_lanes);
  // Read LM size per lane
  uint64_t lane_lm_size;
  loadedBytes = fread(&lane_lm_size, sizeof(uint64_t), 1, spd_file);
  UPDOWN_INFOMSG("LM Dump size per lane (from dump file): %lu", lane_lm_size);

  // FIXME
  // Disable using the pseudo instruction interface due to crash
  // m5_load_udlm(BaseAddrs.spaddr, start_nwid.get_NetworkId_UdName(), num_lanes, filename);

  // Use t2ud_memcpy interface for now. this should be executed before switch_cpus (for fast simulation time)
  fseek(spd_file, dump_start_file_offset, SEEK_SET);
  uint8_t *data = nullptr;
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    // LM specified from the dump
    uint64_t total_lm_size = dump_num_lanes * lane_lm_size;
    data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
    loadedBytes = fread(data, sizeof(uint8_t), total_lm_size, spd_file);
    uint64_t lm_offset = 0;
    for (uint32_t i = dump_start_nwid.get_NetworkId_UdName(); i < dump_start_nwid.get_NetworkId_UdName() + dump_num_lanes; i++) {
      t2ud_memcpy(&data[lm_offset], lane_lm_size, networkid_t(i, false, 0), 0);
      lm_offset += lane_lm_size;
    }
  } else {
    // all LMs
    uint64_t total_lm_size = num_lanes * DEF_SPMEM_BANK_SIZE;
    data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
    loadedBytes = fread(data, sizeof(uint8_t), total_lm_size, spd_file);
    uint64_t lm_offset = 0;
    for (uint32_t i = start_nwid.get_NetworkId_UdName(); i < start_nwid.get_NetworkId_UdName() + num_lanes; i++) {
      t2ud_memcpy(&data[lm_offset], DEF_SPMEM_BANK_SIZE, networkid_t(i, false, 0), 0);
      lm_offset += DEF_SPMEM_BANK_SIZE;
    }
  }

  fclose(spd_file);

  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    return std::make_pair(dump_start_nwid, dump_num_lanes);
  } else {
    return std::make_pair(start_nwid, num_lanes);
  }
#else
  return std::make_pair(networkid_t(0, false, 0), 0);
#endif
}

void *UDRuntime_t::mm_malloc(uint64_t size) {
  UPDOWN_INFOMSG("Calling mm_malloc %lu", size);
  return MappedMemoryManager->get_region(size, false);
}

void *UDRuntime_t::mm_malloc_at_addr(void *addr, uint64_t size) {
  UPDOWN_INFOMSG("Calling mm_malloc_at_addr (%p, %lu)", addr, size);
  return MappedMemoryManager->get_region_at_addr(addr, size, false);
}

void UDRuntime_t::mm_free(void *ptr) {
  UPDOWN_INFOMSG("Calling mm_free  0x%lX", reinterpret_cast<uint64_t>(ptr));
  return MappedMemoryManager->remove_region(ptr, false);
}

void *UDRuntime_t::mm_malloc_global(uint64_t size) {
  UPDOWN_INFOMSG("Calling mm_malloc_global %lu", size);
  return MappedMemoryManager->get_region(size, true);
}

void *UDRuntime_t::mm_malloc_global_at_addr(void *addr, uint64_t size) {
  UPDOWN_INFOMSG("Calling mm_malloc_global_at_addr (%p, %lu)", addr, size);
  return MappedMemoryManager->get_region_at_addr(addr, size, true);
}

void UDRuntime_t::mm_free_global(void *ptr) {
  UPDOWN_INFOMSG("Calling mm_free_global  0x%lX", reinterpret_cast<uint64_t>(ptr));
  return MappedMemoryManager->remove_region(ptr, true);
}

void UDRuntime_t::mm2t_memcpy(uint64_t offset, void *dst, uint64_t size) {
  ptr_t src = BaseAddrs.mmaddr + offset / sizeof(word_t);
  UPDOWN_ASSERT(src + size / sizeof(word_t) < BaseAddrs.mmaddr + MachineConfig.MapMemSize / sizeof(word_t),
                "mm2t_memcpy: memory access to 0x%lX out of mapped memory bounds "
                "with offset %lu bytes and size %lu bytes. Mapped memory Base Address "
                "0x%lX mapped memory size %lu bytes",
                (unsigned long)(BaseAddrs.mmaddr + offset / sizeof(word_t)), (unsigned long)(offset), (unsigned long)size, (unsigned long)BaseAddrs.mmaddr,
                (unsigned long)MachineConfig.MapMemSize);
  UPDOWN_INFOMSG("Copying %lu bytes from mapped memory (0x%lX = %ld) to top (0x%lX = %ld)", size, reinterpret_cast<uint64_t>(src), *src,
                 reinterpret_cast<uint64_t>(dst), *reinterpret_cast<word_t *>(dst));
  std::memcpy(dst, src, size);
}

void UDRuntime_t::t2mm_memcpy(uint64_t offset, void *src, uint64_t size) {
  ptr_t dst = BaseAddrs.mmaddr + offset / sizeof(word_t);
  UPDOWN_ASSERT(dst + size / sizeof(word_t) < BaseAddrs.mmaddr + MachineConfig.MapMemSize / sizeof(word_t),
                "t2mm_memcpy: memory access to 0x%lX out of mapped memory bounds "
                "with offset %lu bytes and size %lu bytes. Mapped memory Base "
                "Address 0x%lX mapped memory size %lu bytes",
                (unsigned long)(BaseAddrs.mmaddr + offset / sizeof(word_t)), (unsigned long)(offset), (unsigned long)size, (unsigned long)BaseAddrs.mmaddr,
                MachineConfig.MapMemSize);
  UPDOWN_INFOMSG("Copying %lu bytes from top (0x%lX = %ld) to mapped memory (0x%lX = %ld)", size, reinterpret_cast<uint64_t>(src),
                 *reinterpret_cast<word_t *>(src), reinterpret_cast<uint64_t>(dst), *dst);
  std::memcpy(dst, src, size);
}

void UDRuntime_t::t2ud_memcpy(void *data, uint64_t size, networkid_t nwid, uint32_t offset) {
  uint64_t apply_offset = get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  UPDOWN_ASSERT(BaseAddrs.spaddr + apply_offset + size / sizeof(word_t) < BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
                "t2ud_memcpy: memory access to 0x%lX out of scratchpad memory bounds "
                "with offset %lu bytes and size %lu bytes. Scratchpad memory Base "
                "Address 0x%lX scratchpad memory size %lu bytes",
                (unsigned long)(BaseAddrs.spaddr + apply_offset), (unsigned long)(apply_offset * sizeof(word_t)), (unsigned long)size,
                (unsigned long)BaseAddrs.spaddr, MachineConfig.SPSize());
  std::memcpy(BaseAddrs.spaddr + apply_offset, data, size);
  UPDOWN_INFOMSG("Copying %lu bytes from Top to Node:%u, Stack:%u, UD %u, "
                 "Lane %u, offset %u, Apply offset %lu. Signal in 0x%lX",
                 size, nwid.get_NodeId(), nwid.get_StackId(), nwid.get_UdId(), nwid.get_LaneId(), offset, apply_offset,
                 reinterpret_cast<uint64_t>(BaseAddrs.spaddr + apply_offset));
}

void UDRuntime_t::ud2t_memcpy(void *data, uint64_t size, networkid_t nwid, uint32_t offset) {
  uint64_t apply_offset = get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  UPDOWN_ASSERT(BaseAddrs.spaddr + apply_offset + size / sizeof(word_t) < BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
                "ud2t_memcpy: memory access to 0x%lX out of scratchpad memory bounds "
                "with offset %lu bytes and size %lu bytes. Scratchpad memory Base "
                "Address 0x%lX scratchpad memory size %lu bytes",
                (unsigned long)(BaseAddrs.spaddr + apply_offset), (unsigned long)(apply_offset * sizeof(word_t)), (unsigned long)size,
                (unsigned long)BaseAddrs.spaddr, MachineConfig.SPSize());
  std::memcpy(data, BaseAddrs.spaddr + apply_offset, size);
  UPDOWN_INFOMSG("Copying %lu bytes from UD %u, Lane %u to Top, offset %u, "
                 "Apply offset %lu. Signal in 0x%lX",
                 size, nwid.get_UdId(), nwid.get_LaneId(), offset, apply_offset, reinterpret_cast<uint64_t>(BaseAddrs.spaddr + apply_offset));
}

bool UDRuntime_t::test_addr(networkid_t nwid, uint32_t offset, word_t expected) {
  uint64_t apply_offset = get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  UPDOWN_ASSERT(BaseAddrs.spaddr + apply_offset < BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
                "test_addr: memory access to 0x%lX out of scratchpad memory bounds "
                "with offset %lu bytes and size 4 bytes. Scratchpad memory Base Address "
                "0x%lX scratchpad memory size %lu bytes",
                (unsigned long)(BaseAddrs.spaddr + apply_offset), (unsigned long)(apply_offset * sizeof(word_t)), (unsigned long)BaseAddrs.spaddr,
                MachineConfig.SPSize());
  UPDOWN_INFOMSG("Testing UD %u, Lane %u to Top, offset %u."
                 " Addr 0x%lX. Expected = %lu, read = %lu",
                 nwid.get_UdId(), nwid.get_LaneId(), offset, reinterpret_cast<uint64_t>(BaseAddrs.spaddr + apply_offset), expected,
                 *(BaseAddrs.spaddr + apply_offset));
  return *(BaseAddrs.spaddr + apply_offset) == expected;
}

void UDRuntime_t::test_wait_addr(networkid_t nwid, uint32_t offset, word_t expected) {
  uint64_t apply_offset = get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  UPDOWN_ASSERT(BaseAddrs.spaddr + apply_offset < BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
                "test_wait_addr: memory access to 0x%lX out of scratchpad memory bounds "
                "with offset %lu bytes and size 4 bytes. Scratchpad memory Base Address "
                "0x%lX scratchpad memory size %lu bytes",
                (unsigned long)(BaseAddrs.spaddr + apply_offset), (unsigned long)(apply_offset * sizeof(word_t)), (unsigned long)BaseAddrs.spaddr,
                MachineConfig.SPSize());
  UPDOWN_INFOMSG("Testing UD %u, Lane %u to Top, offset %u."
                 " Addr 0x%lX. Expected = %lu, read = %lu. (%s)",
                 nwid.get_UdId(), nwid.get_LaneId(), offset, reinterpret_cast<uint64_t>(BaseAddrs.spaddr + apply_offset), expected,
                 *(BaseAddrs.spaddr + apply_offset), *(BaseAddrs.spaddr + apply_offset) != expected ? "Waiting" : "Returning");
  while (*(BaseAddrs.spaddr + apply_offset) != expected)
    ;
}

} // namespace UpDown
