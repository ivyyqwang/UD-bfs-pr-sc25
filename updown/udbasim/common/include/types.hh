/**
**********************************************************************************************************************************************************************************************************************************
* @file:	types.hh
* @author:
* @date:
* @brief:   Basic Types used in BASIM
**********************************************************************************************************************************************************************************************************************************
**/
#include <iostream>

#ifndef __TYPES__H__
#define __TYPES__H__
#include <cstdint>
#include <map>
#include <string>
#include "encodings.hh"
#include "debug.hh"

namespace basim {

#define NUM_GPRS 16
#define NUM_THREADS 255
#define SCRATCHPAD_SIZE 4194304
#define INSTMEM_SIZE 4194304
#define SCRATCHPADBANK_SIZE 65536
#define NUMOBREGS 8
#define NONGPRREGS 16

enum class LdSt : uint8_t { LOAD, STORE };

enum class IncDec : uint8_t { INC, DEC };

union Imm32 {
  uint32_t u;
  int32_t i;
};

union Imm16 {
  uint16_t u;
  int16_t i;
};

union Imm8 {
  uint8_t u;
  int8_t i;
};

typedef LdSt ldst;
typedef IncDec incdec;
typedef uint64_t UIP;
typedef uint64_t Addr;
typedef uint64_t *ptr;
typedef uint64_t word_t;
typedef uint32_t encoded_inst;

#define WORDSIZE 8

/* accessor functions for FSCR */
struct FSCR {
  uint64_t _fscr;
  FSCR() : _fscr(0) {};
  FSCR(uint64_t val) : _fscr(val) {}
  FSCR &operator=(uint64_t val) {
    _fscr = val;
    return *this;
  }
};

enum RdMode{
  SBMODE = 1,
  LMMODE = 0,
};

/* accessor functions for FSCR */
struct SBCR {
  uint64_t _sbcr;
  SBCR(){};
  SBCR(uint64_t val) : _sbcr(val) {}
  SBCR &operator=(uint64_t val) {
    _sbcr = val;
    return *this;
  }
  uint64_t getMaxSBP(){
    return static_cast<uint64_t>(_sbcr & 0xFFFFFFFF);
  }
  void setMaxSBP(uint64_t val){
    _sbcr = ( ((_sbcr>>32)<<32) | (val &0xFFFFFFFF) );
  }
  uint64_t getAdvanceWidth(){
    return static_cast<uint64_t>( (_sbcr >> 32) & 0xF);
  }
  void setAdvanceWidth(uint64_t val){
    _sbcr = ( (_sbcr & 0xFFFFFFF0FFFFFFFF) | (val & 0xF)<<32 );
  } 
  uint64_t getIssueWidth(){
    return static_cast<uint64_t>( (_sbcr >> 36) & 0xF);
  }
  void setIssueWidth(uint64_t val){
    _sbcr = ( (_sbcr & 0xFFFFFF0FFFFFFFFF) | (val & 0xF)<<36 );
  }
  RdMode getRdMode(){
    return static_cast<RdMode>( (_sbcr >> 40) & 0x1);
  }
  void setRdMode(RdMode val){
    _sbcr = ( (_sbcr & 0xFFFFFEFFFFFFFFFF) | (static_cast<uint64_t>(val) & 0x1)<<40 );
  }
};

/* accessor functions for state_property*/
struct stateproperty_t{
  uint64_t _sp;
  stateproperty_t(): _sp(0) {};
  stateproperty_t(uint64_t val): _sp(val) {};
  stateproperty_t &operator=(uint64_t val){
    _sp = val;
    return *this;
  }
  uint64_t getValue(){
    return static_cast<uint64_t>( (_sp & 0xFFF0000) >> 16) ;
  }
  void setValue(uint64_t val){
    _sp = (_sp & 0xFFFF) | ((static_cast<uint64_t>(val) & 0xFFF)<< 16);
  }
  StateProperty getType(){
    return static_cast<StateProperty>(_sp & 0xF);
  }
  void setType(StateProperty prop){
    _sp = (_sp & 0xFFFFFF0) | (static_cast<uint64_t>(prop) & 0xF);
  }
  uint64_t getState(){
    return static_cast<uint64_t> ((_sp & 0xFFF0) >> 4);
  }
  void setState(uint64_t val){
    _sp = (_sp & 0xFFF000F) | ( (static_cast<uint64_t>(val) & 0xFFF) << 4);
  }

  void updateType(TransitionType tt){
    switch(tt){
      case TransitionType::EVENT:
      case TransitionType::EVENTCARRY:
        this->setType(StateProperty::EVENT);
        break;
      case TransitionType::BASIC:
      case TransitionType::BASIC_WITH_ACTION:
        this->setType(StateProperty::BASIC);
        break;
      case TransitionType::FLAGCARRY:
      case TransitionType::FLAGCARRY_WITH_ACTION:
        this->setType(StateProperty::FLAG);
        break;
      case TransitionType::REFILL:
      case TransitionType::REFILL_WITH_ACTION:
        this->setType(StateProperty::BASIC);
        break;
      case TransitionType::COMMONCARRY:
      case TransitionType::COMMONCARRY_WITH_ACTION:
        this->setType(StateProperty::COMMON);
        break;
      case TransitionType::EPSILONCARRY:
      case TransitionType::EPSILONCARRY_WITH_ACTION:
        this->setType(StateProperty::EPSILON);
        break;
      case TransitionType::MAJORITYCARRY:
        this->setType(StateProperty::MAJORITY);
        break;
      case TransitionType::FLAGMAJORITYCARRY:
        this->setType(StateProperty::FLAG_MAJORITY);
        break;
      case TransitionType::DEFAULTCARRY:
        this->setType(StateProperty::DEFAULT);
        break;
      case TransitionType::FLAGDEFAULTCARRY:
        this->setType(StateProperty::FLAG_DEFAULT);
        break;
      default:
        BASIM_ERROR("Invalid Transition Type Encountered");
    }
  }
const char* print_type(StateProperty prop){
  const char * state_type="";
  switch(prop){
    case StateProperty::BASIC:
        state_type = std::string("basic").c_str();
        break; 
    case StateProperty::COMMON:
        state_type = std::string("common").c_str();
        break; 
    case StateProperty::EPSILON:
        state_type = std::string("epsilon").c_str();
        break; 
    case StateProperty::EVENT:
        state_type = std::string("event").c_str();
        break; 
    case StateProperty::FLAG:
        state_type = std::string("flag").c_str();
        break; 
    case StateProperty::NUL:
        state_type = std::string("NULL").c_str();
        break; 
    //case StateProperty::REFILL:
    //    state_type = std::string("refill").c_str();
    //    break; 
    case StateProperty::DEFAULT:
        state_type = std::string("default").c_str();
        break; 
    case StateProperty::FLAG_DEFAULT:
        state_type = std::string("flag_default").c_str();
        break; 
    case StateProperty::MAJORITY:
        state_type = std::string("majority").c_str();
        break; 
    case StateProperty::FLAG_MAJORITY:
        state_type = std::string("flag_majority").c_str();
        break; 
    default:
        BASIM_ERROR("Invalid State Type Encountered");
    }
    return state_type;
}
};

/**
 * Union for Register Value since we have unified registers
 * Both signed and unsigned types used and should be used based on context in instructions
 * uVal<n>b - unsigned int packed nbits
 * iVal<n>b - signed int packed nbits
 */

typedef word_t regval_t;

/**
 * Type Conversion helper functions from gem5 (src/base/types.hh)
 * we need these since our registers are unified
 */
static inline uint32_t floatToBits32(float val) {
  union {
    float f;
    uint32_t i;
  } u;
  u.f = val;
  return u.i;
}

static inline uint64_t floatToBits64(double val) {
  union {
    double f;
    uint64_t i;
  } u;
  u.f = val;
  return u.i;
}

static inline uint64_t floatToBits(double val) { return floatToBits64(val); }
static inline uint32_t floatToBits(float val) { return floatToBits32(val); }

static inline float bitsToFloat32(uint32_t val) {
  union {
    float f;
    uint32_t i;
  } u;
  u.i = val;
  return u.f;
}

static inline double bitsToFloat64(uint64_t val) {
  union {
    double f;
    uint64_t i;
  } u;
  u.i = val;
  return u.f;
}

static inline double bitsToFloat(uint64_t val) { return bitsToFloat64(val); }
static inline float bitsToFloat(uint32_t val) { return bitsToFloat32(val); }

} // namespace basim
#endif //!__TYPES__H__
