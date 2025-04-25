/**
**********************************************************************************************************************************************************************************************************************************
* @file:	tstable.hh
* @author:	Andronicus
* @date:
* @brief:   Header File for the Thread State Table
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __TSTABLE__H__
#define __TSTABLE__H__
#include "threadstate.hh"
#include <iostream>
#include <map>
#include <vector>
#include <algorithm> // for std::sort

namespace basim {

class TSTable {
private:
  /* thread state map */
  std::map<uint32_t, ThreadStatePtr> _tstable;

  /* Free TIDs*/
  std::vector<uint32_t> freetids;

  /* NWID */
  NetworkID nwid;

public:
  /* Constructor sets up list of free tids*/
  TSTable(NetworkID nwid): nwid(nwid) {
    for (int i = 0; i < NUM_THREADS; i++) {
      freetids.emplace_back(i);
    }
  }

  TSTable(): nwid(NetworkID()) {
    for (int i = 0; i < NUM_THREADS; i++) {
      freetids.emplace_back(i);
    }
  }

  uint32_t getTID() {
    if (freetids.size() > 0) {
      uint32_t tid = freetids[0];
      freetids.erase(freetids.begin(), freetids.begin() + 1);
      return tid;
    } else {
      BASIM_ERROR("[NWID %u] No Free Threads available", nwid.networkid);
    }
  }

  void reorder_freetids() {
        std::sort(freetids.begin(), freetids.end());
  }

  void addtoTST(ThreadStatePtr tsptr) { _tstable[tsptr->getTID()] = tsptr; }

  void remfromTST(uint32_t tid) {
    freetids.push_back(tid);
    auto it = _tstable.find(tid);
#ifndef BASIM_STANDALONE
    delete it->second;
#endif
    _tstable.erase(it);
  }

  ThreadStatePtr getThreadState(uint32_t tid) {
    auto it = _tstable.find(tid);
    if (it == _tstable.end())
      return nullptr;
    return it->second;
  }

  bool noThreadsActive() { return (freetids.size() == NUM_THREADS); }
  
  uint64_t numActiveThreads() { return static_cast<uint64_t>(NUM_THREADS) - static_cast<uint64_t>(freetids.size()); }

  //~TSTable(){
  //    delete freetids;
  //    delete _tstable;
  //}
};
typedef TSTable *TSTablePtr;

} // namespace basim

#endif //!__TSTABLE__H__
