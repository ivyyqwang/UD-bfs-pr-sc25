/**
 * @file upstream_obj.cc
 * @author Andronicus
 * @brief Definition of a simple upstream object
 * @version 0.1
 * @date 2021-10-25
 *
 * @copyright Copyright (c) 2021
 * Adapted from downstream_obj.cc by Jose Monsalve Diaz
 * This file is based on the simple_cache.cc
 * example in the learning_gem5 folder.
 * The following Copyright applies:
 * Copyright (c) 2017 Jason Lowe-Power
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
 *
 */

#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>

#include "compatibility.h"
#include "debug.h"
#include "sim_stats.hh"
#include "upstream_pyintf.hh"

PUSHWARNING(deprecated-declarations)

Upstream_PyIntf::Upstream_PyIntf() { udid = 0; }

void Upstream_PyIntf::addSystemPaths() {
  UPDOWN_INFOMSG("Adding system paths: %s",
                 "\"./emulator:" UPDOWN_INSTALL_DIR
                 "/emulator:" UPDOWN_SOURCE_DIR "/emulator\"");
  PyRun_SimpleString("import sys\nsys.path.append(\".\")\n");
  PyRun_SimpleString("import sys\nsys.path.append(\"./emulator\")\n");
  PyRun_SimpleString("import sys\nsys.path.append(\"" UPDOWN_SOURCE_DIR
                     "/emulator \")\n");
  PyRun_SimpleString("import sys\nsys.path.append(\"" UPDOWN_INSTALL_DIR
                     "/emulator\")\n");
}

Upstream_PyIntf::~Upstream_PyIntf() {
  Py_DECREF(pEmulator);
  PyObject_CallMethod(pVirtEngine, "__del__", "()");
  Py_DECREF(pVirtEngine);
  //Py_Finalize();
}

Upstream_PyIntf::Upstream_PyIntf(uint32_t nwid, uint32_t ud_idx, uint32_t numlanes,
                                 std::string progfile, std::string efaname,
                                 std::string simdir, int lm_addr_mode,
                                 uint32_t lmsize, uint64_t lmbase, std::string outdir,
                                 uint64_t freq, int print_level,
                                 long print_threshold, bool perf_log_enable,
                                 bool perf_log_internal_enable) {
  this->udid = ud_idx;
  PyObject *pargs, *pclass_ve, *pefa_util, *pEfafile, *pefa;
  PyObject *res_init;

  //Py_Initialize();

  addSystemPaths();

  pEmulator = PyImport_ImportModule("EfaExecutor_v2");
  if (pEmulator == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Error when loading pEmulator");
    std::exit(1);
  }
  pefa_util = PyObject_GetAttrString(pEmulator, "efa_util");
  if (pefa_util == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Error when loading efa_util");
    std::exit(1);
  }
  PyObject_CallMethod(pefa_util, "printLevel", "(i)", print_level);
  PyObject_CallMethod(pefa_util, "printThreshold", "(L)", print_threshold);

  // def __init__(self, lane_id, numOfGpr, dram_mem, top, perf_file):
  UPDOWN_INFOMSG("Creating UpStream PyIntf with %ld lanes %u banksize",
                 numlanes, lmsize);
  pclass_ve = PyObject_GetAttrString(pEmulator, "VirtualEngine");
  if (pclass_ve == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Error when loading pclass_ve");
    std::exit(1);
  }
  // TODO: This output should be relative to CWD
  std::string perffile = "output/perf_stats.txt";

  

  // Arguments are:
  // nwid, ud_idx, num_lanes, perf_file, sim, lmbanksize, scratchpad_base,
  // tick_freq, simout_dir='./', perf_log_enable=0, perf_log_internal_enable=0):
  pargs =
      Py_BuildValue("(Iiisiillsii)", nwid, ud_idx, numlanes,
                    perffile.c_str(), 1, lmsize, lmbase, freq, outdir.c_str(),
                    perf_log_enable, perf_log_internal_enable);
  pVirtEngine = PyEval_CallObject(pclass_ve, pargs);
  if (pVirtEngine == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Error when loading pVirtEngine");
    std::exit(1);
  }

  UPDOWN_INFOMSG("Initialized UpStream Python Interface with %s and %s",
                 progfile.c_str(), efaname.c_str());
  const char *pfile = progfile.c_str();
  const char *pname = efaname.c_str();
  const char *simprefix = simdir.c_str();
  pEfafile = PyImport_ImportModule(pfile);
  if (pEfafile == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Error when loading pEfafile");
    std::exit(1);
  }
  pefa = PyObject_CallMethod(pEfafile, pname, nullptr);

  if (pefa == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Error when loading pefa");
    std::exit(1);
  }
  UPDOWN_INFOMSG("UpStream PyIntf, EFA created ");

  res_init = PyObject_CallMethod(pVirtEngine, "setup_sim", "(Osi)", pefa,
                                 simprefix, lm_addr_mode);
  if (res_init == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Error when calling setup_sim");
    std::exit(1);
  }

  Py_DECREF(pefa_util);
  Py_DECREF(pargs);
  Py_DECREF(pclass_ve);
  Py_DECREF(pEfafile);
  Py_DECREF(pefa);
  Py_DECREF(res_init);
  UPDOWN_INFOMSG("UpStream Processor Setup_Sim done ");
}

void Upstream_PyIntf::insert_event(uint64_t edata, int numOb, int lane_id) {
  PyObject *pclass_ev, *res, *pargs_e, *pstart_event;
  pclass_ev = PyObject_GetAttrString(pEmulator, "Event");
  uint64_t eword = edata;
  int elabel = eword & 0xfffff;
  int tid = (eword >> 24) & 0xff;
  // int lane_num = (eword >> 24) & 0x3f;
  uint64_t nwid = (uint64_t)(eword >> 32) & 0xffffffff;
  int tmode = (eword >> 23) & 0x1;

  pargs_e = Py_BuildValue("(ii)", elabel, numOb);
  pstart_event = PyEval_CallObject(pclass_ev, pargs_e);
  res = PyObject_CallMethod(pstart_event, "setmode", "(i)", tmode);
  res = PyObject_CallMethod(pstart_event, "setnetworkid", "(I)", nwid);
  res = PyObject_CallMethod(pstart_event, "setthreadid", "(i)", tid);
  res = PyObject_CallMethod(pVirtEngine, "insert_event", "(iO)", lane_id,
                            pstart_event);
  UPDOWN_INFOMSG(
      "Pushed Event:%d, lane:%d, tid:%d numop:%d  actual-numop:%d, tmode:%d",
      elabel, lane_id, tid, numOb - 2, numOb, tmode);
  Py_DECREF(res);
  Py_DECREF(pargs_e);
  Py_DECREF(pstart_event);
  Py_DECREF(pclass_ev);
}

void Upstream_PyIntf::insert_operand(uint64_t odata, int lane_id) {
  PyObject *res;
  res = PyObject_CallMethod(pVirtEngine, "insert_operand", "(iL)", lane_id,
                            odata);

  UPDOWN_INFOMSG("Lane:%d Pushed into Operand Buffer: %ld", lane_id, odata);
  Py_DECREF(res);
}

void Upstream_PyIntf::set_print_level(int printLvl) {
  PyObject *efautil_ev = PyObject_GetAttrString(pEmulator, "efa_util");
  PyObject_CallMethod(efautil_ev, "printLevel", "(i)", printLvl);
  Py_DECREF(efautil_ev);
}

void Upstream_PyIntf::insert_scratch(uint32_t saddr, uint64_t sdata) {
  PyObject *res;
  res = PyObject_CallMethod(pVirtEngine, "write_scratch", "(iL)", saddr, sdata);

  UPDOWN_INFOMSG("Entered into ScratchPad 0x%X 0x%lX", saddr, sdata);
  Py_DECREF(res);
}

void Upstream_PyIntf::insert_sbuffer(uint32_t saddr, uint64_t sdata,
                                     int lane_id) {
  PyObject *res = PyObject_CallMethod(pVirtEngine, "write_sbuffer", "(iLi)",
                                      saddr, sdata, lane_id);
  Py_DECREF(res);
}

void Upstream_PyIntf::read_scratch(uint32_t saddr, uint8_t *data,
                                   uint32_t size) {
  PyObject *res_scratch;
  UPDOWN_INFOMSG("Reading %d bytes, from address (%u)0x%X, into pointer 0x%lX",
                 size, saddr, saddr, reinterpret_cast<uint64_t>(data));
  if (size == 1) {
    res_scratch =
        PyObject_CallMethod(pVirtEngine, "read_scratch", "(ii)", saddr, size);
    if (res_scratch == nullptr) {
      PyErr_Print();
      UPDOWN_ERROR("Read_scratch Error: Return object NULL");
      exit(1);
    }
    *data = (uint8_t)PyLong_AsLong(res_scratch);
  } else if (size == 2) {
    res_scratch =
        PyObject_CallMethod(pVirtEngine, "read_scratch", "(ii)", saddr, size);
    if (res_scratch == nullptr) {
      PyErr_Print();
      UPDOWN_ERROR("Read_scratch Error: Return object NULL");
      exit(1);
    }
    uint16_t temp = (uint16_t)PyLong_AsLong(res_scratch);
    data[0] = temp & 0xff;
    data[1] = (temp >> 8) & 0xff;
  } else if (size == 4) {
    res_scratch =
        PyObject_CallMethod(pVirtEngine, "read_scratch", "(ii)", saddr, size);
    if (res_scratch == nullptr) {
      PyErr_Print();
      UPDOWN_ERROR("Read_scratch Error: Return object NULL");
      exit(1);
    }
    uint32_t temp = (uint32_t)PyLong_AsLong(res_scratch);
    data[0] = temp & 0xff;
    data[1] = (temp >> 8) & 0xff;
    data[2] = (temp >> 16) & 0xff;
    data[3] = (temp >> 24) & 0xff;

  } else if (size > 4) {
    uint32_t locaddr = saddr;
    int num8bytes = size / 8;
    for (int i = 0; i < num8bytes; i++) {
      res_scratch =
          PyObject_CallMethod(pVirtEngine, "read_scratch", "(ii)", locaddr, 8);
      if (res_scratch == nullptr) {
        PyErr_Print();
        UPDOWN_ERROR("Read_scratch Error: Return object NULL");
        exit(1);
      }
      uint64_t temp = (uint64_t)PyLong_AsUnsignedLong(res_scratch);
      if (temp == 0xffffffffffffffff)
        temp = -1;
      data[8 * i + 0] = temp & 0xff;
      data[8 * i + 1] = (temp >> 8) & 0xff;
      data[8 * i + 2] = (temp >> 16) & 0xff;
      data[8 * i + 3] = (temp >> 24) & 0xff;
      data[8 * i + 4] = (temp >> 32) & 0xff;
      data[8 * i + 5] = (temp >> 40) & 0xff;
      data[8 * i + 6] = (temp >> 48) & 0xff;
      data[8 * i + 7] = (temp >> 56) & 0xff;
      locaddr += 8;
    }
  }
  Py_DECREF(res_scratch);
}

void Upstream_PyIntf::read_sbuffer(uint32_t saddr, uint8_t *data, uint32_t size,
                                   int lane_id) {
  PyObject *res;
  if (size == 1) {
    res = PyObject_CallMethod(pVirtEngine, "read_sbuffer", "(iii)", saddr, size,
                              lane_id);
    *data = (uint8_t)PyLong_AsLong(res);
  } else if (size == 2) {
    res = PyObject_CallMethod(pVirtEngine, "read_sbuffer", "(iii)", saddr, size,
                              lane_id);
    uint16_t temp = (uint16_t)PyLong_AsLong(res);
    data[0] = temp & 0xff;
    data[1] = (temp >> 8) & 0xff;
  } else if (size == 4) {
    res = PyObject_CallMethod(pVirtEngine, "read_sbuffer", "(iii)", saddr, size,
                              lane_id);
    UPDOWN_ERROR_IF(res == nullptr,
                    "Read_Stream Buffer Error: Return object NULl\n");
    uint32_t temp = (uint32_t)PyLong_AsLong(res);
    data[0] = temp & 0xff;
    data[1] = (temp >> 8) & 0xff;
    data[2] = (temp >> 16) & 0xff;
    data[3] = (temp >> 24) & 0xff;

  } else {
    UPDOWN_ERROR(
        "Cannot read from Upstream LM - if not aligned to 4bytes > 4Bytes\n");
  }
  Py_DECREF(res);
}

uint32_t Upstream_PyIntf::getEventQ_Size(int lane_id) {
  PyObject *res_eq;
  res_eq = PyObject_CallMethod(pVirtEngine, "getEventQ_size", "(i)", lane_id);
  if (res_eq == nullptr) {
    UPDOWN_ERROR("EventQ Size: Return object NULL");
    exit(1);
  }
  uint32_t evq_size = (uint32_t)PyLong_AsLong(res_eq);
  Py_DECREF(res_eq);
  return evq_size;
}

uint32_t Upstream_PyIntf::getPolicyLane(int lane_id, uint32_t policy) {
  PyObject *res_eq;
  res_eq = PyObject_CallMethod(pVirtEngine, "get_lane_by_policy", "(ii)",
                               lane_id, policy);
  if (res_eq == nullptr) {
    UPDOWN_ERROR("PolicyLane: Return object NULL");
    exit(1);
  }
  uint32_t policy_lane = (uint32_t)PyLong_AsLong(res_eq);
  Py_DECREF(res_eq);
  return policy_lane;
}

void Upstream_PyIntf::dumpEventQueue(int lane_id) {
  PyObject_CallMethod(pVirtEngine, "dumpEventQ", "(i)", lane_id);
}

int Upstream_PyIntf::execute(int cont_state, struct SimStats &stats,
                             int lane_id, unsigned long timestamp) {
  const char *arg = "O";
  const int NUM_RETURN_ITEMS = 35;
  PyObject *res_exec, *return_items[NUM_RETURN_ITEMS];
  PyObject *fname = Py_BuildValue("s", "executeEFA_simAPI");
  PyObject *flaneid = Py_BuildValue("i", lane_id);
  PyObject *ftimestamp = Py_BuildValue("L", timestamp);
  res_exec = PyObject_CallMethodObjArgs(pVirtEngine, fname, flaneid, ftimestamp,
                                        nullptr);
  if (res_exec == nullptr) {
    PyErr_Print();
    UPDOWN_ERROR("Execute Error: Return object NULL");
    exit(1);
  } else {
    int ok;

    for (int i = 0; i < NUM_RETURN_ITEMS; i++) {
      return_items[i] = PyTuple_GetItem(res_exec, i);
      Py_INCREF(return_items[i]);
    }

    uint32_t return_state = (uint32_t)PyLong_AsLong(return_items[1]);
    stats.cur_num_sends = (uint64_t)PyLong_AsLongLong(return_items[0]);
    stats.num_sends = (uint64_t)PyLong_AsLongLong(return_items[0]);
    stats.exec_cycles = (uint64_t)PyLong_AsLongLong(return_items[2]);
    stats.total_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[3]);
    stats.idle_cycles = (uint64_t)PyLong_AsLongLong(return_items[4]);
    stats.lm_read_bytes = (uint64_t)PyLong_AsLongLong(return_items[5]);
    stats.lm_write_bytes = (uint64_t)PyLong_AsLongLong(return_items[6]);
    stats.send_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[7]);
    stats.move_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[8]);
    stats.branch_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[9]);
    stats.alu_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[10]);
    stats.yield_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[11]);
    stats.compare_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[12]);
    stats.cmp_swp_inst_cnt = (uint64_t)PyLong_AsLongLong(return_items[13]);
    stats.transition_cnt = (uint64_t)PyLong_AsLongLong(return_items[14]);
    stats.event_queue_max = (uint64_t)PyLong_AsLongLong(return_items[15]);
    stats.event_queue_mean = (double)PyFloat_AsDouble(return_items[16]);
    stats.operand_queue_max = (uint64_t)PyLong_AsLongLong(return_items[17]);
    stats.operand_queue_mean = (double)PyFloat_AsDouble(return_items[18]);
    for (int i = 0; i < 16; i++) {
      stats.user_counter[i] = (uint64_t)PyLong_AsLongLong(return_items[19 + i]);
    }

    auto cur_exec_cycles = stats.exec_cycles;
    auto cur_actcnt = stats.total_inst_cnt;

    UPDOWN_INFOMSG(
        "EFA execute output, LaneID:%d, Return State:%d, Num Sends: %ld\
                            Exec_cycles:%ld, Actcnt:%ld ",
        lane_id, return_state, stats.cur_num_sends, cur_exec_cycles,
        cur_actcnt);
    Py_DECREF(res_exec);
    for (int i = 0; i < NUM_RETURN_ITEMS; i++) {
      Py_DECREF(return_items[i]);
    }
    Py_DECREF(flaneid);
    Py_DECREF(ftimestamp);
    Py_DECREF(fname);
    return return_state;
  }
}

POPWARNING