#ifndef UPSTREAM_PYINTF_HH
#define UPSTREAM_PYINTF_HH

extern "C" {
#include "Python.h"
}

class Upstream_PyIntf {
private:
  uint32_t udid;
  PyObject *pEmulator, *pVirtEngine;

  /**
   * @brief Adds system paths for searching the necessary modules
   *
   * This function adds the following system locations to the python
   * system path:
   *
   * - Installation path for updown runtime lib emulator
   * - Source code location for updown runtime lib emulator
   * - A folder named emulator in the current location
   *
   */
  void addSystemPaths();
  void updown_perf_log_close();

public:
  Upstream_PyIntf();
  Upstream_PyIntf(uint32_t nwid, uint32_t ud_idx, uint32_t numlanes,
                  std::string progfile, std::string efaname, 
                  std::string simdir, int lm_addr_mode,
                  uint32_t lmsize, uint64_t lmbase, std::string outdir, uint64_t freq,
                  int print_level, long print_start, bool perf_log_enable,
                  bool perf_log_internal_enable);
  void insert_event(uint64_t edata, int numOb, int lane_id);
  void insert_operand(uint64_t odata, int lane_id);

  void set_print_level(int printLvl);

  int execute(int cont_state, struct SimStats &stats, int lane_id,
              unsigned long timestamp);

  void insert_scratch(uint32_t saddr, uint64_t sdata);
  void insert_sbuffer(uint32_t saddr, uint64_t sdata, int lane_id);
  void read_scratch(uint32_t saddr, uint8_t *data, uint32_t size);
  void read_sbuffer(uint32_t saddr, uint8_t *data, uint32_t size, int lane_id);

  uint32_t getEventQ_Size(int lane_id);
  uint32_t getPolicyLane(int lane_id, uint32_t policy);
  void dumpEventQueue(int lane_id);

  void finalizeVirtualEngine();

  /*
   * Simple Wrapper for upstream emulator Virtual engine
   */
  ~Upstream_PyIntf();
};

#endif // UPSTREAM_LANE_HH
