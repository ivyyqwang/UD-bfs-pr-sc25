/**
**********************************************************************************************************************************************************************************************************************************
* @file:	opbuffer.hh
* @author:	Andronicus
* @date:
* @brief:   Class Definition for the UpDown Operand Buffer
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __OPBUFFER__H__
#define __OPBUFFER__H__
#include "lanetypes.hh"
#include "types.hh"
#include <cstdlib>
#include <deque>
#include <iostream>

namespace basim {
template <typename T> class OpBuffer {
private:
  /* OpBuffer data */
  std::deque<T> _data;

  /* Capacity */
  size_t _capacity;

  /* Class Name*/
  const char *_name;

public:
  /**
   * @brief Construct a new OpBuffer Object
   *
   * @param size Size of the Queue, 0 - infinite
   */
  OpBuffer(size_t size = 0) : _capacity(size), _name(__FUNCTION__) {}

  //~OpBuffer(){~_data;}

  /**
   * @brief Push operand into OpBuffer
   *
   * @param word sized operand
   */
  bool push(T operand) {
    // capacity == 0 indicates infinite operand buffer
    if (_data.size() < _capacity || (_capacity == 0)) {
      _data.push_back(operand);
      return true;
    }
    return false;
  }
  /**
   * @brief Clear numOp operands from OpBuffer
   *
   * @param 
   */
  bool clear(uint8_t numOp) {
    uint8_t toClear = numOp;
    while (_data.size() > 0 && toClear > 0) {
      _data.pop_front();
      toClear--;
    }
    if (toClear > 0)
      return false;
    return true;
  }

  /**
   * @brief Read Operand Buffer at index
   *
   * @param 64bit event word - event
   */

  T read(uint32_t idx) { return _data[idx]; }

  /**
   * @brief Get current size of Operand Buffer
   *
   */

  size_t getSize(void) { return _data.size(); }
  /**
   * @brief Get Buffer Capacity
   *
   */

  size_t getCapacity(void) { return _capacity; }

  /**
   * @brief Get name of object type (for debug logging)
   *
   */

  const char *name(void) { return _name; }
};

typedef OpBuffer<operands_t> *OpBufferPtr;
} // namespace basim

#endif //!__OPBUFFER__H__
