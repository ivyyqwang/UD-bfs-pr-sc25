#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string.h>
#include <utility>

#include "debug.h"

namespace UpDown {

/**
 * @brief Class that holds information about the operands.
 *
 * Contains a pointer to data and the number of operands.
 * data is an array of ptr_t, representing each word in the
 * operand buffer when copied.
 *
 *
 */
class operands_t {
private:
  // Number of operands 8 bits long. Up to 256 operands are allowed
  uint8_t NumOperands;
  // Pointer to the data to consider operands. Consecutive array of operands
  ptr_t Data;

public:
  /**
   * @brief Construct a new empty operands_t object
   *
   * Set the Data pointer to null and NumOperands to 0
   */
  operands_t() : NumOperands(0), Data((ptr_t)malloc(sizeof(word_t))) {
    Data[0] = 0;
  }

  /**
   * @brief Copy Constructor
   *
   * @param o other object
   */
  operands_t(const operands_t &o)
      : NumOperands(o.NumOperands),
        Data((ptr_t)malloc(sizeof(word_t) * (NumOperands + 1))) {
    // Copy the data
    if (NumOperands != 0)
      std::memcpy(o.Data, Data, sizeof(word_t) * (NumOperands + 1));
  }

  /**
   * @brief Copy Constructor
   *
   * @param o other object
   */
  operands_t(operands_t &&o) : NumOperands(o.NumOperands), Data(o.Data) {
    // Reset the other operand's pointer
    o.Data = nullptr;
  }

  /**
   * @brief Construct a new operands_t opbejct, setting the operands
   *
   * @param num Number of operaqnds
   * @param oper Operand value
   * @param cont Continuation event
   *
   * @todo This should avoid using memcpy
   */
  operands_t(uint8_t num, ptr_t oper, word_t cont = 0)
      : NumOperands(num),
        Data((ptr_t)malloc(sizeof(word_t) *
                           (NumOperands + 1))) { // TODO: Avoid this malloc

    Data[0] = cont; // Fake continuation
    std::memcpy(Data + 1, oper, get_NumOperands() * sizeof(word_t));
  }

  /**
   * @brief Construct a new operands_t opbejct,
   *
   * @param num Number of operaqnds
   * @param cont Continuation event
   *
   * @todo This should avoid using memcpy
   */
  operands_t(uint8_t num, word_t cont = 0)
      : NumOperands(num),
        Data((ptr_t)malloc(sizeof(word_t) *
                           (NumOperands + 1))) { // TODO: Avoid this malloc
    Data[0] = cont;
  }

  /**
   * @brief Get the pointer to Data
   *
   * @return ptr_t pointer to data
   */
  ptr_t get_Data() { return Data; }

  /**
   * @brief Set an operand
   *
   * @param op operand number
   * @param val value for the operand
   */
  template <class T> inline void set_operand(uint64_t op, T val) {
    static_assert(sizeof(T) <= sizeof(word_t));
    Data[op + 1] = 0;
    memcpy(&Data[op + 1], &val, sizeof(T));
  }

  /**
   * @brief Set multiple operands at once
   *
   * Example:
   *
   * ```C
   * // Mapping a struct to different operands
   * // Assume no padding
   *
   * struct A {
   *  word_t v1; // 4 bytes
   *  word_t v2; // 4 bytes
   *  int * ptr; // 8 bytes
   * };
   *
   * // Assuming word_t is 4 bytes,
   * // size of A should be 16 bytes, using
   * // 4 elements in the operand buffer
   * int anInt;
   * A myStr = {1, 2, &anInt};
   * rt.set_operands(0,4, &myStr);
   *
   * // the struct will be copied bit a bit, each
   * // operand in a different location.
   * ```
   *
   * @param op_begin Start operand inclusive
   * @param op_end End operand inclusive
   * @param val pointer to the value to be copied
   *
   *
   */
  inline void set_operands(uint64_t op_begin, uint64_t op_end, void *val) {
    std::memcpy(Data + op_begin + 1, val, (op_end - op_begin) * sizeof(word_t));
  }

  /**
   * @brief Set the Continuation
   *
   * @param cont
   */
  inline void set_cont(word_t cont) { Data[0] = cont; }

  /**
   * @brief Get the NumOperands
   *
   * @return uint8_t number of operands
   */
  uint8_t get_NumOperands() { return NumOperands; }

  ~operands_t() { free(Data); }
};

} // namespace UpDown