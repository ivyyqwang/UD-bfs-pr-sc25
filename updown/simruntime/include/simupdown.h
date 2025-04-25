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
 *
 */

#ifndef UPDOWNSIM_H
#define UPDOWNSIM_H
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <new>
#include <string>
#include <utility>
#include <vector>

#include "debug.h"
#include "sim_stats.hh"
#include "updown.h"

#ifndef UPDOWN_INSTALL_DIR
#define UPDOWN_INSTALL_DIR "."
#endif

#ifndef UPDOWN_SOURCE_DIR
#define UPDOWN_SOURCE_DIR "."
#endif

class Upstream_PyIntf;
namespace UpDown {

/**
 * @brief Control emulator log print level
 *
 * This flag uses the EfaUtil.py printing interface
 * to set the level of printing in the execution of the emulator.
 */
enum EmulatorLogLevel {
  FULL_TRACE = 0,
  STAGE_TRACE = 1,
  PROGRESS_TRACE = 2,
  NONE = 5,
};

/**
 * @brief Wrapper class that allows simulation of runtime calls
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


class SimUDRuntime_t : public UDRuntime_t {

protected:
  const std::string LogFileName = "Perf.log";
  uint8_t *MappedMemory;
  uint8_t *GMappedMemory;
  uint8_t *ScratchpadMemory;
  uint8_t *ControlMemory;

  /// This controls how many iterations of UDP can progress before
  /// the control is return to the top thread.
  /// You can set up this value with the environment variable
  /// UPDOWN_SIM_ITERATIONS. If set to 0, the updown will not
  /// return until all events are executed
  uint64_t max_sim_iterations = 100;

  std::string programFile;
  std::string programName;
  std::string simulationDir;

private:
  Upstream_PyIntf **upstream_pyintf;
  /// When python is not enabled, we bypass all the calls to the python
  /// interface. This restricts simulation to only memory operations
  /// Contains a mapped memory to the file system that is used to communicate
  /// with the emulator.
  uint32_t **sendmap = nullptr;

protected:
  bool python_enabled;
  uint32_t total_uds;


  /// Container for the stats for all UpDown lanes in the system
  std::vector<std::vector<struct SimStats>> simStats;

  /**
   * @brief Initialize the stats for all the UpDowns
   */
  void init_stats();
  /**
   * @brief Allocate memory for the simulation of the updown
   *
   * This function allocates the MappedMemory, the Scratchpad memory
   * and the Control Memory, used for the simulation. Then it changes
   * the MachineConfig object to use these pointers instead of the
   * default ones for these three memory regions.
   *
   * @todo We are allocating the whole address space. We could behave more
   * like a driver and translate it to the actual available memory.
   * This means. It should not allocate the reserved space for expansion.
   */
  void initMemoryArrays();

  /**
   * @brief Initialize interface with python emulator
   *
   * This function handles initialization of the interface with python
   * EFA emulator. The emulator is in charge of UpDown behavior.
   *
   * @param printLevel Printing level for the python emulator
   * @param perf_log_enabling Currently for gem5 only?
   *
   * @todo when increasing the number of lanes to multiple UpDowns, this
   * function must be re-implemented
   */
private:
  void initPythonInterface(EmulatorLogLevel printLevel,
                           bool perf_log_enable = false,
                           bool perf_log_internal_enable = false);

  void executeSingleLane(uint8_t ud_id, uint8_t lane_num);

public:
  /**
   * @brief Construct a new SimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. Python will be disabled. Only simulating memory interactions.
   *
   */
  SimUDRuntime_t();

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
  SimUDRuntime_t(ud_machine_t machineConfig);

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
  SimUDRuntime_t(std::string programFile, std::string programName,
                 std::string simulationDir,
                 EmulatorLogLevel printLvl = EmulatorLogLevel::NONE);

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
  SimUDRuntime_t(ud_machine_t machineConfig, std::string programFile,
                 std::string programName, std::string simulationDir,
                 EmulatorLogLevel printLvl = EmulatorLogLevel::NONE);

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
  SimUDRuntime_t(ud_machine_t machineConfig, std::string programFile,
                 std::string programName);

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
  SimUDRuntime_t(ud_machine_t machineConfig, std::string programFile);

  /**
   * @brief Wrapper function for send_event
   *
   * Calls the emulator and calls the UDRuntime_t::send_event() function
   */
  void send_event(event_t ev) override;

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

  ~SimUDRuntime_t();

  void update_stats(struct SimStats &locstats, uint32_t ud_id,
                    uint8_t lane_num);

  void print_stats(uint32_t ud_id, uint8_t lane_num);
};

} // namespace UpDown

#endif
