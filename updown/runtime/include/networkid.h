#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <utility>

#include "debug.h"

namespace UpDown {

/**
 * @brief Contains encoding of hardware structures in UpDown System
 *
 * This class constructs the networkID description. The networkID are
 * the MSB of the event word, and they describe a unique location in
 * the system. There are two formats that can be enconded in the
 * networkID. This is determined by the TopUd bit.
 *
 * # Top/UD = 0 (UD Network IDs):
 * * Lane (6 bits)
 * * UDs (2 bits)
 * * Stack (3 bits)
 * * Node (16 bits)
 * * Send Policy (3 bits)
 *
 * # Top/UD = 1 (Top core or LLC Network IDs):
 * * Core or LLC ID (5 bits)
 * * Core Structures (3 bits): Cache/Prefetch buffer/Load-store queues
 * * Operation (3 bits): Invalidate, write, etc...
 * * Node (16 bits)
 *
 * @todo: Add encoding for top network elements
 */

union networkid_t {
  uint32_t v = 0;

  struct {
    uint32_t lane_id    : 6;   // [5:0]                                                    
    uint32_t udid       : 2;   // [7:6]                                                    
    uint32_t stack_id   : 3;   // [10:8]                                                   
    uint32_t nodeid     : 16;  // [26:11]                                                  
    uint32_t sendpolicy : 4;   // [30:27]                                                  
    uint32_t topud      : 1;   // [31]                                                     
  } f;

  networkid_t() { v = 0; }

  networkid_t( uint32_t nwid ) { v = nwid; }

  networkid_t(
    uint8_t lane_id, uint8_t udid, uint8_t stack_id = 0, uint16_t nodeid = 0, uint8_t topud = 0, uint8_t sendpolicy = 0
  ) {
    f.lane_id    = lane_id & 0x3f;
    f.udid       = udid & 0x3;
    f.stack_id   = stack_id & 0x7;
    f.nodeid     = nodeid & 0xffff;
    f.sendpolicy = sendpolicy & 0x2;
    f.topud      = topud & 0x1;
    print();
  }

  networkid_t( uint32_t ud_name, bool topud, uint8_t sendpolicy ) {
    v            = ud_name & 0x7ffffffUL;
    f.topud      = topud;
    f.sendpolicy = sendpolicy;
    print();
  }


  void print() {
    UPDOWN_INFOMSG(
      "Creating a new network id TopUd = %d, SendPolicy = %d, NodeId = %d, "
      "StackId=%d, UDId = 0x%X, lane_id=%d, network_id=0x%X",
      f.topud,                                                                           
      f.sendpolicy,
      f.nodeid,
      f.stack_id,
      f.udid,
      f.lane_id,
      v
    );
  }

  // setters and getters
  uint32_t get_NetworkId() { return v; }
  uint32_t get_NetworkId_UdName() { return v & 0x7ffffffUL; }
  uint8_t get_LaneId() { return f.lane_id; }
  uint8_t get_UdId() { return f.udid; }
  uint8_t get_StackId() { return f.stack_id; }
  uint16_t get_NodeId() { return f.nodeid; }
  uint8_t get_SendPolicy() { return f.sendpolicy; }
  uint8_t get_TopUd() { return f.topud; }
  void set_SendPolicy(uint8_t sendpolicy) { f.sendpolicy = sendpolicy & 0x2; }
};


} // namespace UpDown