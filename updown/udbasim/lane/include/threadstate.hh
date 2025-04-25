/**
**********************************************************************************************************************************************************************************************************************************
* @file:	threadstate.hh
* @author:	Andronicus
* @date:
* @brief:   Thread State that goes into Thread State Table
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __THREADSTATE__H__
#define __THREADSTATE__H__
#include "encodings.hh"
#include "lanetypes.hh"
#include "types.hh"
#include <iomanip>
#include <iostream>
#include <memory>

namespace basim {

class ThreadState {
private:
  /* Thread ID */
  uint8_t _tid;

  /* Network ID X0*/
  NetworkID _nwid;

  /* Network ID X1*/
  eventword_t _current_cont;

  /* Network ID X2*/
  eventword_t _current_event;

  // X3 is operand 8

  /* FSCR X4 */
  FSCR _fscr;

  /* SBCR X4 */
  SBCR _sbcr;

  /* SBCR X5 */
  regval_t _sbp;

  /* state_property X6*/
  // StateProperty _stateproperty;
  stateproperty_t _stateproperty;

  /* state_property X7*/
  Addr _lmbase;
  int _lmMode;

  /* X8 - X15, X3 operands */
  std::shared_ptr<operands_t> _ob;

  /* X16 - X31 UD program registers (simple array) */
  std::unique_ptr<regval_t[]> _udprs;

  /* Program Base address */
  Addr _pgbase;

  /* Thread Mode - Regular/Streaming*/
  bool _tmode;

public:
  ThreadState() : _tid(0), _nwid(0), _udprs(nullptr), _lmMode(0) {}
  ThreadState(uint8_t tid, NetworkID nwid, Addr lmbase, Addr pgbase, int lmMode = 0) : _tid(tid), _nwid(nwid), _lmbase(lmbase), _pgbase(pgbase), _lmMode(lmMode) {
    _udprs = std::unique_ptr<regval_t[]>(new regval_t[NUM_GPRS]);
    _stateproperty = stateproperty_t(0);
    BASIM_INFOMSG("NWID:%u, TID:%u, Creating a new Thread", _nwid.networkid, _tid);
  }

  uint8_t getTID() { return _tid; }
  uint32_t getNWIDbits() { return _nwid.networkid; }
  eventword_t getEventWord() { return _current_event; }
  eventword_t getContinuationWord() { return _current_cont; }

  /* Read Register  */
  regval_t readReg(RegId rid);

  /* General register access functions*/

  /* Write Thread State Register  */
  void writeReg(RegId rid, regval_t data);

  /* Special register access functions*/
  /* Update event word  */
  void writeEvent(eventword_t ev) { _current_event = ev; }

  /* Update continuation  */
  void writeContinuation(eventword_t cont) { _current_cont = cont; }

  /* Update Operands  */
  void writeOperands(operands_t opers) {
    _ob = std::make_shared<operands_t>(opers);
    if(opers[0] != 0x7FFFFFFFFFFFFFFF)
      _current_cont = EventWord(opers[0]);
  }

  // Setting Thread mode on creation
  void setTmode(bool tmode){
    _tmode = tmode;
  }

  // Setting State property at initialization of thread based onmode
  void setStateProperty(stateproperty_t sp){
    _stateproperty = sp;
  }
  
  stateproperty_t getStateProperty(){
    return _stateproperty;
  }
  
  void setSBCR(SBCR sbcr){
    _sbcr = sbcr;
  }
  
  SBCR getSBCR(){
    return _sbcr;
  }

  void setMaxSBP(regval_t data){
    _sbcr.setMaxSBP(data);
  }

  Addr getMaxSBP(){
    return _sbcr.getMaxSBP();
  }

};

typedef ThreadState *ThreadStatePtr;

} // namespace basim

#endif //!__THREADSTATE__H__
