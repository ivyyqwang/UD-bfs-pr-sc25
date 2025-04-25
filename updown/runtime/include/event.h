#pragma once

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <utility>

#include "debug.h"

#include "networkid.h"
#include "operands.h"

namespace UpDown {

/**
 * @brief Contains information of an event in the UpDown.
 *
 * This class constructs the information of the event word based on
 * each of its parameters. It also contains a pointer to the operands
 * that is used when sending the event.
 *
 * @todo UpDown ID is not being used
 * @todo, event_t considers a 4 byte word size
 */

union packed_evt_t {
  uint64_t v = 0xffUL << 24;

  struct {
    uint64_t elabel      : 20;  // [15:0]
    uint64_t numoperands : 3;   // [22:20] //TODO the mask operator, 4, looks wrong
    uint64_t threadmode  : 1;   // [23]
    uint64_t tid         : 8;   // [31:24]
    uint64_t nwid        : 32;  // [63:32]
  } f;

  packed_evt_t() : v( 0xffUL << 24 ) { print(); }

  packed_evt_t( uint32_t _v ) : v( _v ) { print(); }

  packed_evt_t( uint32_t elabel, networkid_t& nwid, uint8_t tid = CREATE_THREAD, operands_t* operands = nullptr ) {
    if( operands ) {
      assert( operands->get_NumOperands() >= 2 );
    }
    f.nwid        = nwid.v;
    f.tid         = tid;
    f.threadmode  = 0;
    f.numoperands = operands ? operands->get_NumOperands() - 2 : 0;  // encoded
    f.elabel      = elabel;
    print();
  }

private:
  void print() {
    UPDOWN_INFOMSG(
      "Creating a new event label = %d, network_id = 0x%x, "
      "thread_id = %d, encoded_num_operands(numOperands-2) = %d, ev_word = 0x%lx",
      f.elabel,
      f.nwid,
      f.tid,
      f.numoperands,
      v
    );
  }
};

class event_t {
private:
  packed_evt_t EventWord = {};
  operands_t*  Operands  = nullptr;  // Operands to be sent with this event

public:
  word_t get_EventWord() { return EventWord.v; }

  operands_t* get_Operands() { return Operands; }

  void set_operands( operands_t* ops ) { Operands = ops; }

  networkid_t get_NetworkId() { return (networkid_t) EventWord.f.nwid; }

  uint8_t get_ThreadId() { return EventWord.f.tid; }

  uint32_t get_EventLabel() { return EventWord.f.elabel; }

  void set_EventLabel( uint32_t label ) { EventWord.f.elabel = ( label & 0xfffff ); }

  uint8_t get_NumOperands() { return ( Operands != nullptr ) ? Operands->get_NumOperands() : 0; }

  uint8_t get_EncodedNumOperands() { return EventWord.f.numoperands; }

  ptr_t get_OperandsData() { return ( Operands != nullptr ) ? Operands->get_Data() : nullptr; }

  /**
   * @brief Construct a new empty event object
   *
   */

  event_t() {
    Operands  = {};
    EventWord = {};
  };

  /**
   * @brief Construct a new event_t object
   *
   * @param e_label Event label ID
   * @param nwid Network ID representing Lane, Updown, Node, etc
   * @param tid Thread ID
   * @param operands Pointer to operands. Must be pre-initialized
   */
  event_t( uint32_t e_label, networkid_t nwid, uint8_t tid = CREATE_THREAD, operands_t* operands = nullptr ) {
    Operands  = operands;
    EventWord = { e_label, nwid, tid, operands };
  }

  /**
   * @brief Set the event word object with new values
   *
   * @param e_label the ID of the event in the updown
   * @param noperands the number of operands
   * @param lid Lane ID
   * @param tid Thread ID
   */
  void set_event( uint32_t e_label, networkid_t nwid, uint8_t tid = CREATE_THREAD, operands_t* operands = nullptr ) {
    Operands  = operands;
    EventWord = { e_label, nwid, tid, operands };
  }

#if 1
  event_t( event_t& rhs ) {
    EventWord = rhs.EventWord;
    Operands  = rhs.Operands;
  }

  event_t( event_t&& ) = default;

  event_t& operator=( event_t& rhs ) {
    EventWord = rhs.EventWord;
    Operands  = rhs.Operands;
    return *this;
  }

  event_t& operator=( event_t&& ) = default;
#endif
};

}  // namespace UpDown
