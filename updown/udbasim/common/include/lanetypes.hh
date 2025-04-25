/**
**********************************************************************************************************************************************************************************************************************************
* @file:	lanetypes.hh
* @author:	Andronicus
* @date:
* @brief:   Basic Types used inside the Lane/Accel
**********************************************************************************************************************************************************************************************************************************
**/
#include "debug.hh"
#include "types.hh"
#include "cmath"
#include <iostream>
#include <iomanip>
#include <memory>
#include <ostream>

#ifndef __LANETYPES__H__
#define __LANETYPES__H__

namespace basim {

// Helper masks
#define HIGH32_64B 0xFFFFFFFF00000000
#define LOW32_64B 0x00000000FFFFFFFF
// defines for network id
#define LANEMASK 0x3F
#define UDMASK 0xC0
#define STACKMASK 0x700
#define NODEMASK 0x7FFF800
#define POLICYMASK 0x30000000
#define TOPUDMASK 0x80000000
#define LANENEGMASK 0xFFFFFFC0
#define UDNEGMASK 0xFFFFFF3F
#define STACKNEGMASK 0xFFFFF8FF
#define NODENEGMASK 0x80007FF
#define POLICYNEGMASK 0xCFFFFFFF
#define TOPUDNEGMASK 0x7FFFFFFF
#define LANEBITS 0x3F
#define UDBITS 0x3
#define STACKBITS 0x7
#define NODEBITS 0xFFFF
#define POLICYBITS 0x7
#define TOPUDBITS 0x1
#define LANEPOS 0
#define UDPOS 6
#define STACKPOS 8
#define NODEPOS 11
#define POLICYPOS 27
#define TOPUDPOS 31

// defines for eventword
#define NWIDMASK 0xFFFFFFFF00000000
#define THREADIDMASK 0xFF000000
#define THREADMODEMASK 0x00800000
#define NUMOPMASK 0x00700000
#define ELABELMASK 0x000FFFFF
#define NWIDNEGMASK 0x00000000FFFFFFFF
#define THREADIDNEGMASK 0xFFFFFFFF00FFFFFF
#define THREADMODENEGMASK 0xFFFFFFFFFF7FFFFF
#define NUMOPNEGMASK 0xFFFFFFFFFF8FFFFF
#define ELABELNEGMASK 0xFFFFFFFFFFF00000
#define NWIDPOS 32
#define THREADIDPOS 24
#define THREADMODEPOS 23
#define NUMOPPOS 20
#define ELABELPOS 0
#define NWIDBITS 0xFFFFFFFF
#define THREADIDBITS 0xFF
#define THREADMODEBITS 0x1
#define NUMOPBITS 0x7
#define ELABELBITS 0xFFFFF

// endianness
#define LITTLEENDIAN

// Send Buffer Latency 
#define SENDLAT 0
// #define BIGENDIAN

// EventQ threshold
#define EVENTQTHRESHOLD 1024
#define MAX_Q_SIZE 131072


// Shared block fixed addresses
#define REFILLBLOCK 0xF4 // 4*61
#define TERMBLOCK 0x0 // 4*0
#define SBSIZE 64 // 64 bytes
#define EFABASEMASK 0xFFFFFFFFFFFFC000

#define WORDALIGN 0xFFFFFFFFFFFFFFF8
/* UD Machine types */
/**
 * @brief Network ID for Lanes with accessor functions
 *
 * @todo: Add encoding for top network elements
 */
struct NetworkID {
  uint32_t networkid; // Complete networkID encoded
  /**
   * @brief Construct a new network id
   *
   */
  NetworkID() : networkid(0){};
  NetworkID(uint32_t val) : networkid(val) {
    BASIM_INFOMSG("Network id TopUd = %d, "
                  "SendPolicy = %d, NodeId = %d, StackId=%d, UDId = 0x%X, "
                  "lane_id=%d, network_id=0x%X",
                  this->getTopUD(), this->getSendPolicy(), this->getNodeID(), this->getStackID(), this->getUDID(), this->getLaneID(), val);
  }
  NetworkID &operator=(uint32_t val) {
    networkid = val;
    return *this;
  }

  uint32_t getUDName() { return networkid & (NODEMASK | STACKMASK | UDMASK | LANEMASK); }

  void setUDName(uint32_t udname) { networkid = (networkid & NODENEGMASK & STACKNEGMASK & UDNEGMASK & LANENEGMASK) | (udname & (NODEMASK | STACKMASK | UDMASK | LANEMASK)); }

  /* get Lane ID from NetworkID */
  uint8_t getLaneID() { return static_cast<uint8_t>(((networkid >> LANEPOS) & LANEBITS)); }

  /* set Lane ID in NetworkID */
  void setLaneID(uint8_t lid) { networkid = (networkid & LANENEGMASK) | (static_cast<uint32_t>(lid) & LANEMASK); }

  /* get UDID from NetworkID */
  uint8_t getUDID() { return static_cast<uint8_t>(((networkid >> UDPOS) & UDBITS)); }

  /* set UDID ID in NetworkID */
  void setUDID(uint8_t udid) { networkid = (networkid & UDNEGMASK) | ((static_cast<uint32_t>(udid) << UDPOS) & UDMASK); }

  /* get cluster / stack ID from NetworkID */
  uint8_t getStackID() { return static_cast<uint8_t>((networkid >> STACKPOS) & STACKBITS); }

  /* set StackID ID in NetworkID */
  void setStackID(uint8_t stackid) { networkid = (networkid & STACKNEGMASK) | ((static_cast<uint32_t>(stackid) << STACKPOS) & STACKMASK); }

  /* get Node ID from NetworkID */
  uint16_t getNodeID() { return static_cast<uint16_t>((networkid >> NODEPOS) & NODEBITS); }

  /* set StackID ID in NetworkID */
  void setNodeID(uint32_t nodeid) { networkid = (networkid & NODENEGMASK) | ((nodeid << NODEPOS) & NODEMASK); }

  /* get Send policy from NetworkID */
  uint8_t getSendPolicy() { return static_cast<uint8_t>((networkid >> POLICYPOS) & POLICYBITS); }

  /* set Send policy in NetworkID */
  void setSendPolicy(uint8_t SendPolicy_) { networkid = (networkid & POLICYNEGMASK) | ((static_cast<uint32_t>(SendPolicy_) << POLICYPOS) & POLICYMASK); }

  /* get Top/UD bit from NetworkID */
  uint8_t getTopUD() { return static_cast<uint8_t>((networkid >> TOPUDPOS) & TOPUDBITS); }

  /* set TOPUD/bit */
  void setTOPUD(uint8_t topud) { networkid = (networkid & TOPUDNEGMASK) | ((topud << TOPUDPOS) & TOPUDMASK); }
};

inline std::ostream &operator<<(std::ostream &str, NetworkID &nwid) {
      str << "NetworkID: 0x" << nwid.networkid << ", Node:" << nwid.getNodeID() << ", Stack:"
          << nwid.getStackID() << "UD:" << nwid.getUDID() << ", Lane:" << nwid.getLaneID() << "Policy:" << nwid.getSendPolicy() << std::dec;
      return str;
}


typedef NetworkID networkid_t;
/**
 * @brief Event Word and accessor functions
 *
 * @todo:
 */
struct EventWord {
  uint64_t eventword; // Complete networkID encoded
  EventWord() : eventword(0){};
  EventWord(uint64_t val) : eventword(val) {
    BASIM_INFOMSG("Creating a new event label = %u, network_id = %u, "
                  "thread_id = %u, encoded_num_operands = %u, actual_operands = %u, ev_word = 0x%lx",
                  this->getEventLabel(), this->getNWIDbits(), this->getThreadID(), this->getNumOperands(), this->getNumOperands() + 2, val);
  }
  EventWord &operator=(uint64_t val) {
    eventword = val;
    return *this;
  }
  // get NetworkID from event_word
  NetworkID getNWID() { return NetworkID(static_cast<uint32_t>(((eventword) >> NWIDPOS) & NWIDBITS)); }
  
  // get NetworkID Bits from event_word
  uint32_t getNWIDbits() { return ((eventword >> NWIDPOS) & NWIDBITS ); }

  // set NetworkID using nwid struct
  void setNWID(NetworkID nwid) { eventword = (eventword & NWIDNEGMASK) | ((static_cast<uint64_t>(nwid.networkid) << NWIDPOS) & NWIDMASK); }

  // set NetworkID using bits
  void setNWIDbits(uint32_t nwid) { eventword = (eventword & NWIDNEGMASK) | ((static_cast<uint64_t>(nwid) << NWIDPOS) & NWIDMASK); }

  // get ThreadID from event_word
  uint8_t getThreadID() { return (static_cast<uint8_t>((eventword) >> THREADIDPOS) & THREADIDBITS); }

  // set ThreadID in event_word
  void setThreadID(uint8_t tid) { eventword = (eventword & THREADIDNEGMASK) | ((static_cast<uint64_t>(tid) << THREADIDPOS) & THREADIDMASK); }

  // get ThreadMode from event_word
  uint8_t getThreadMode() { return (static_cast<uint8_t>((eventword) >> THREADMODEPOS) & THREADMODEBITS); }

  // set ThreadMode in event_word
  void setThreadMode(uint8_t tmode) { eventword = (eventword & THREADMODENEGMASK) | ((static_cast<uint64_t>(tmode) << THREADMODEPOS) & THREADMODEMASK); }

  // get NumOperands from event_word
  uint8_t getNumOperands() { return static_cast<uint8_t>((eventword >> NUMOPPOS) & NUMOPBITS); }

  // set NumOperands in event_word
  void setNumOperands(uint8_t numop) { eventword = (eventword & NUMOPNEGMASK) | ((static_cast<uint64_t>(numop) << NUMOPPOS) & NUMOPMASK);}

  // get Eventlabel from event_word
  uint32_t getEventLabel() { return (eventword & ELABELBITS); }

  // set Eventlabel in event_word
  void setEventLabel(uint32_t elabel) { eventword = (eventword & ELABELNEGMASK) | (static_cast<uint64_t>(elabel << ELABELPOS) & ELABELMASK); }

};

inline std::ostream &operator<<(std::ostream &str, EventWord &eword) {
      str << "EventWord: 0x" << std::hex << eword.eventword << ", NWID: 0x" << eword.getNWIDbits() << ", ThreadID: 0x"
          << eword.getThreadID() << "ThreadMode: 0x" << eword.getThreadMode() << ", NumOperands: 0x" << eword.getNumOperands() << "EventLabel :0x" << eword.getEventLabel() << std::dec;
      return str;
}

typedef EventWord eventword_t;
typedef EventWord *eventwordptr_t;

/**
 * @brief Collective operands struct
 *
 * @todo:
 */
struct Operands {
  /* operands per event will always just be one size */
  word_t operands[12];

  /* number of operands */
  int numoperands;

  /* default constructor */
  Operands() : numoperands(0){};

  /* constructor with number of operands */
  Operands(int numop) : numoperands(numop+1){operands[0] = 0;};
  
  Operands(int numop, eventword_t cont) : numoperands(numop+1){
    operands[0] = cont.eventword;
  }

  void setNumOperands(int numop){
    numoperands = numop+1;
    operands[0] = 0;
  }

  /* set the data in the operands container*/
  void setData(word_t *data) {
    for (auto i = 1; i < numoperands; i++){
      operands[i] = data[i-1];
    }
  }

  void setDataWord(int i, word_t data) {
      operands[i+1] = data;
  }

  Operands& operator=(const Operands &that) {
    if(this == &that)
      return *this;
    this->numoperands = that.numoperands;
    //this->operands = that.operands;
    //new word_t[that.numoperands];
    for (int i = 0; i < that.numoperands; i++) {
      this->operands[i] = that.operands[i];
    }
    return *this;
  }

  /* Overload subscript for easy operand data access */
  uint64_t &operator[](int i) {
    if (i >= 0 && i < numoperands) {
      return operands[i];
    } else {
      // add fatal message here
      BASIM_ERROR("Operand index out of bounds, accessing index %d", i);
    }
  }
//  ~Operands(){
//#ifndef BASIM_STANDALONE    
//    delete[] operands;
//#endif
//  }

};

typedef Operands operands_t;
typedef Operands *operandsptr_t;

#ifdef INST_HIST
enum class InstMap : uint32_t {
  // I-Type
  ADDI = 0,
  SUBI = 1,
  MULI = 2,
  DIVI = 3,
  MODI = 4,
  CLTI = 5,
  CGTI = 6,
  CEQI = 7,
  ANDI = 8,
  ORI = 9,
  XORI = 10,
  MOVIL2 = 11,
  MOVIL1 = 12,
  YIELD = 13,
  YIELDT = 14,
  LASTACT = 15,
  SLI = 16,
  SRI = 17,
  SLORI = 18,
  SRORI = 19,
  SLANDI = 20,
  SRANDI = 21,
  SARI = 22,
  HASHSB32 = 23,
  HASHSB64 = 24,
  HASHL64 = 25,
  HASH = 26,
  HASHL = 27,
  BCPYLLI = 28,
  MOVSBR = 29,
  MOVIPR = 30,
  MOVLSB = 31,
  SIW = 32,
  REFILL = 33,
  SSPROP = 34,
  // LI-Type
  EVLB = 35,
  MOVIR = 36,
  // P-Type
  PRINT = 37,
  PERFLOG = 38,
  // S-Type
  SLADDII = 39,
  SLSUBII = 40,
  SRADDII = 41,
  SRSUBII = 42,
  SLORII = 43,
  SRORII = 44,
  SLANDII = 45,
  SRANDII = 46,
  MOVBIL = 47,
  MOVBLR = 48,
  FSTATE = 49,
  CSWPI = 50,
  MOVLR = 51,
  MOVRL = 52,
  SWIZ = 53,
  BCPYOLI = 54,
  // R-Type
  ADD = 55,
  SUB = 56,
  MUL = 57,
  DIV = 58,
  MOD = 59,
  AND = 60,
  OR = 61,
  XOR = 62,
  CLT = 63,
  CGT = 64,
  CEQ = 65,
  CSTR = 66,
  SR = 67,
  SL = 68,
  SAR = 69,
  BCPYLL = 70,
  MOVRR = 71,
  MOVWLR = 72,
  MOVWRL = 73,
  BCPYOL = 74,
  FMADD_64 = 75,
  FADD_64 = 76,
  FSUB_64 = 77,
  FMUL_64 = 78,
  FDIV_64 = 79,
  FSQRT_64 = 80,
  FEXP_64 = 81,
  FMADD_32 = 82,
  FADD_32 = 83,
  FSUB_32 = 84,
  FMUL_32 = 85,
  FDIV_32 = 86,
  FSQRT_32 = 87,
  FEXP_32 = 88,
  FMADD_B16 = 89,
  FADD_B16 = 90,
  FSUB_B16 = 91,
  FMUL_B16 = 92,
  FDIV_B16 = 93,
  FSQRT_B16 = 94,
  FEXP_B16 = 95,
  FCNVT_64_I64 = 96,
  FCNVT_32_I32 = 97,
  FCNVT_I64_64 = 98,
  FCNVT_I32_32 = 99,
  FCNVT_64_32 = 100,
  FCNVT_64_B16 = 101,
  FCNVT_32_64 = 102,
  FCNVT_32_B16 = 103,
  FCNVT_B16_64 = 104,
  FCNVT_B16_32 = 105,
  VMADD_32 = 106,
  VADD_32 = 107,
  VSUB_32 = 108,
  VMUL_32 = 109,
  VDIV_32 = 110,
  VSQRT_32 = 111,
  VEXP_32 = 112,
  VMADD_B16 = 113,
  VADD_B16 = 114,
  VSUB_B16 = 115,
  VMUL_B16 = 116,
  VDIV_B16 = 117,
  VSQRT_B16 = 118,
  VEXP_B16 = 119,
  VMADD_I32 = 120,
  VADD_I32 = 121,
  VSUB_I32 = 122,
  VMUL_I32 = 123,
  VDIV_I32 = 124,
  VSQRT_I32 = 125,
  VEXP_I32 = 126,
  VGT_32 = 127,
  VGT_B16 = 128,
  VGT_I32 = 129,
  // B-Type
  BNE = 130,
  BEQ = 131,
  BGT = 132,
  BLE = 133,
  BNEU = 134,
  BEQU = 135,
  BGTU = 136,
  BLEU = 137,
  BNEI = 138,
  BEQI = 139,
  BGTI = 140,
  BLEI = 141,
  BLTI = 142,
  BGEI = 143,
  BNEIU = 144,
  BEQIU = 145,
  BGTIU = 146,
  BLEIU = 147,
  BLTIU = 148,
  BGEIU = 149,
  // J-Type
  JMP = 150,
  // M1-Type
  SEND = 151,
  SENDB = 152,
  // M2-Type
  SENDM = 153,
  SENDMB = 154,
  INSTRANS = 155,
  // M3-Type
  SENDR = 156,
  SENDR3 = 157,
  SENDMR = 158,
  SENDMR2 = 159,
  // M4-Type
  SENDOPS = 160,
  SENDMOPS = 161,
  // E-Type
  EVI = 162,
  EVII = 163,
  // R4-Type
  EV = 164,
  CSWP = 165,
  // VF-Type
  VFILL_32 = 166,
  VFILL_I32 = 167,
  VFILL_B16 = 168,
  BTAKEN = 169,
  BNTAKEN = 170,
  COUNT = 171,
};

#endif 

enum class LaneState{
  NULLSTATE,
  EVENT_ACTION,
  TRANS,
  TRANS_ACTION,
  TRANS_MAJORITY,
  TRANS_DEFAULT,
  SBREFILL_TERM,
  SBREFILL_TERM_ACTION,
};

enum class SBState{
  TERM,
  REFILL,
  AVAIL,
};

//Struct for current transition with accessor methods
struct CurrentTrans{
  TransitionType transtype; // Current Transition type
  uint8_t attach; // attach 
  uint32_t target;  // target
  uint8_t signature;  // target
  uint64_t state_id;  // stateid
  bool carry; // Carry? 
  bool withAction; // HasAction?
  uint16_t numActions; // To use for action based counting
  Addr actionBaseUIP;
  uint8_t scalar;
  uint8_t base;
  uint8_t mode_refill;
  uint64_t curr_symbol;
  stateproperty_t nextSp; // State Property for next state
  CurrentTrans(){};
  CurrentTrans(uint32_t trans, bool eventTX){
    transtype = static_cast<TransitionType>((trans >> 8) & 0xF);
    attach = static_cast<uint8_t>(trans & 0xFF);
    if(eventTX){
      target = static_cast<uint32_t>(trans >> 12); // 20 bits
      //state_id = target & 0xFFF;
      state_id = (target >> 2) & 0xFFF;
      //target = static_cast<uint32_t>(trans >> 14); // 20 bits 
      signature = 0;
    } else{
      target = static_cast<uint32_t>((trans >> 12) & 0xFFF); // 12 bits
      state_id = target;
      signature = static_cast<uint8_t>((trans >> 24) & 0xFF); // 8 bits
    }
    if(
        transtype == TransitionType::EVENTCARRY ||
        transtype == TransitionType::EVENT ||
        transtype == TransitionType::EPSILONCARRY_WITH_ACTION ||
        transtype == TransitionType::BASIC_WITH_ACTION ||
        transtype == TransitionType::REFILL_WITH_ACTION ||
        transtype == TransitionType::FLAGCARRY_WITH_ACTION ||
        transtype == TransitionType::COMMONCARRY_WITH_ACTION )
      withAction = true;
    else
      withAction = false;
    carry = true; // ALL transitions are carry forward types (set state property action can change the carried dispatch type)
    nextSp.setState(state_id);
    nextSp.updateType(transtype);
    nextSp.setValue(attach);
    // Calculate the numActions based on attach
    if(transtype != TransitionType::REFILL_WITH_ACTION && transtype != TransitionType::REFILL){
      scalar = attach & 0x7;
      base = (attach >> 3) & 0x7;
      mode_refill = (attach >> 6) & 0x3;
    }
    else{
      scalar = attach & 0x3;
      base = (attach >> 2) & 0x7;
      mode_refill = (attach >> 5) & 0x7;
    }
    numActions = static_cast<uint16_t>(pow(2, scalar));

    //BASIM_INFOMSG("CurrentTrans signature:%d target:%d, state_id:%d, attach:%d (mod/refill,base,scalar):(%d,%d,%d)",signature,target,state_id,attach,mode_refill,base,scalar );
    // baseUIP - default value?

  }
  TransitionType getType(){return transtype;}
  void setType(TransitionType _transtype){transtype = _transtype;}
  uint8_t getAttachModeRefill(){return mode_refill;}
  void setAttachModeRefill(uint8_t val){ mode_refill= val; }
  uint8_t getAttachBase(){return base;}
  uint8_t getAttach(){return attach;}
  uint8_t getAttachScalar(){return scalar;}
  uint64_t getStateID(){return static_cast<uint64_t>(state_id);}
  uint8_t getSignature(){return signature;}
  uint64_t getTarget(){return static_cast<uint64_t>(target);}
  bool isCarry(){return carry;}
  bool hasAction(){return withAction;}
  void updateNextSp(stateproperty_t sp){nextSp = sp;}
  stateproperty_t getNextSp(){return nextSp;}
  void setActionBaseUIP(Addr buip){actionBaseUIP = buip;}
  Addr getActionBaseUIP(){return actionBaseUIP;}
  uint16_t getNumActions(){return numActions;}
  void setCurrSymbol(uint64_t symbol){curr_symbol = symbol;}
  uint64_t getCurrSymbol(){return curr_symbol;}
}; 

typedef LaneState lanestate_t;
typedef lanestate_t *lanestateptr;

/**
 * @brief Combined event and operands for push functions
 *
 * @todo:
 */
struct EventOperands {
  /* Pointer to event object */
  eventwordptr_t eventword;

  /* Pointer to operands object */
  operandsptr_t operands;

  /* Default constructor */
  EventOperands() : eventword(nullptr), operands(nullptr){};

  /* Assign the event and operand objects */
  EventOperands(eventwordptr_t evptr, operandsptr_t opptr) : eventword(evptr), operands(opptr){};
};
typedef EventOperands eventoperands_t;

// Let's start with a simple single tick per clk - If we have multiple freq domains ever
// we can move to the gem5 style Clock
typedef uint64_t Tick;

// Function that returns current value of global tick
// getCurTick();

/* piggy backing on gem5's Cycle class */
class Cycles {
private:
  /** Member holding the actual value. */
  uint64_t c;

public:
  /** Explicit constructor assigning a value. */
  explicit constexpr Cycles(uint64_t _c) : c(_c) {}

  /** Default constructor for parameter classes. */
  Cycles() : c(0) {}

  /** Converting back to the value type. */
  constexpr operator uint64_t() const { return c; }

  /** Prefix increment operator. */
  Cycles &operator++() {
    ++c;
    return *this;
  }

  /** Prefix decrement operator. Is only temporarily used in the O3 CPU. */
  Cycles &operator--() {
    assert(c != 0);
    --c;
    return *this;
  }

  /** In-place addition of cycles. */
  Cycles &operator+=(const Cycles &cc) {
    c += cc.c;
    return *this;
  }
  
  /** Comparison operator */
  constexpr bool operator==(const Cycles &cc) {
    return (c == cc.c);
  }

  /** Greater than comparison used for > Cycles(0). */
  constexpr bool operator>(const Cycles &cc) const { return c > cc.c; }

  /** Increment Cycles  */
  constexpr Cycles operator+(const Cycles &b) const { return Cycles(c + b.c); }

  /** Decrement Cycles If diff > 0  */
  constexpr Cycles operator-(const Cycles &b) const { return c >= b.c ? Cycles(c - b.c) : throw std::invalid_argument("RHS cycle value larger than LHS"); }

  /** Multiply cycles by powers of 2  */
  constexpr Cycles operator<<(const int32_t shift) const { return Cycles(c << shift); }

  /** Divide cycles by powers of 2  */
  constexpr Cycles operator>>(const int32_t shift) const { return Cycles(c >> shift); }

  /** friend function for stream  */
  friend std::ostream &operator<<(std::ostream &out, const Cycles &cycles) {
    out << cycles.c;
    return out;
  }
};

} // namespace basim

#endif //!__TYPES__H__
