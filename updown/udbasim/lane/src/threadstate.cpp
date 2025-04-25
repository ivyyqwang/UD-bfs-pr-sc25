#include "threadstate.hh"
#include "debug.hh"
#include "encodings.hh"
#include "types.hh"
#include <cstdint>
#include <math.h>

namespace basim {

/* Read Thread State Register  */
regval_t ThreadState::readReg(RegId rid) {
  uint64_t readval;
  switch (rid) {
  case RegId::X0:
    readval = _nwid.networkid;
    break;
  case RegId::X1:
    readval = _current_cont.eventword;
    break;
  case RegId::X2:
    readval = _current_event.eventword;
    break;
  case RegId::X4:
    readval = _fscr._fscr;
    break;
  case RegId::X5:
    readval = _sbp;
    break;
  case RegId::X6:
    readval = static_cast<regval_t>(_stateproperty._sp);
    break;
  case RegId::X7:
    if(_lmMode){
      readval = _lmbase + ((_nwid.getLaneID()) << 16);
    }else{
      readval = _lmbase;
    }
    break;
  case RegId::X8:
  case RegId::X9:
  case RegId::X10:
  case RegId::X11:
  case RegId::X12:
  case RegId::X13:
  case RegId::X14:
  case RegId::X15:
    readval = (*_ob.get())[static_cast<uint8_t>(rid) - 8 + 1]; // rid is 0 ... 31 +1 since 0 is continuation
    break;
  case RegId::X3:
    if((*_ob.get()).numoperands < 10)
      readval = 0;
    else
      readval = (*_ob.get())[9]; // 0 - continuation, 1-8 - operands, 9 - addr
    break;
  default:
    readval = _udprs[static_cast<uint8_t>(rid) - 16];
  }
#ifdef DEBUG_INST_TRACE
  BASIM_PRINT("NWID:%u, TID:%u, Read Reg:%d:%lu (u)", _nwid.networkid, _tid, static_cast<int>(rid), readval)
#endif
  BASIM_INFOMSG("NWID:%u, TID:%u, Read Reg:%d:%lu (u)", _nwid.networkid, _tid, static_cast<int>(rid), readval)
  return(readval);
}

/* Write Thread State Register  */
void ThreadState::writeReg(RegId rid, regval_t data) {
#ifdef DEBUG_INST_TRACE
  BASIM_PRINT("NWID:%u, TID:%u, Write Reg:%d:%lu (u)", _nwid.networkid, _tid, static_cast<int>(rid), data)
#endif
  BASIM_INFOMSG("NWID:%u, TID:%u, Write Reg:%d:%lu (u)", _nwid.networkid, _tid, static_cast<int>(rid), data)
  switch (rid) {
  case RegId::X0:
    _nwid = data;
    break;
  case RegId::X1:
    _current_cont = EventWord(data);
    break;
  case RegId::X2:
    _current_event = EventWord(data);
    break;
  case RegId::X4:
    _fscr = FSCR(data);
    _sbcr = SBCR(data);
    break;
  case RegId::X5:
    _sbp = data;
    break;
  case RegId::X6:
    // _stateproperty = static_cast<StateProperty>(data);
    _stateproperty = static_cast<stateproperty_t>(data);
    break;
  case RegId::X7:
    _lmbase = data;
    break;
  case RegId::X3:
  case RegId::X8:
  case RegId::X9:
  case RegId::X10:
  case RegId::X11:
  case RegId::X12:
  case RegId::X13:
  case RegId::X14:
  case RegId::X15:
    printf("NWID:%u, TID:%u Attempt to write into Operand Buffer",  _nwid.networkid, _tid);
    exit(1);
    break;
  default:
    _udprs[static_cast<uint8_t>(rid) - 16] = data;
  }
}

} // namespace basim
