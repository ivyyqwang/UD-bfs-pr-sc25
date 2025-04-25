#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>
#include <vector>
#include <string>
#include "basim.hh"

#define USAGE    \
  "USAGE: ./sendr_test <binaryfile> <numlanes>"

using namespace basim;

int main(int argc, char *argv[]) {
  char* testname;
  uint32_t num_lanes;
  if (argc < 3) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  testname = argv[1];
  num_lanes = atoi(argv[2]);

  machine_t machine;
  machine.NumLanes = num_lanes;
  machine.NumNodes = 1;
  machine.NumUDs = 1;
  machine.NumStacks = 1;
  machine.LocalMemAddrMode = 1;

  int lane_num = 0;
  int last_lane_checked = 0;

  word_t ops_data[2];
  BASim rt(machine);
  // UpDown::UDRuntime_t rt(machine);
  rt.initMachine(testname, 0);
  rt.initMemoryArrays();

  printf("Starting launch of events\n");
  for(int i = 0; i < num_lanes; i++){
      operands_t op0(2);
      op0.setDataWord(0, i);
      op0.setDataWord(1, i);
      eventword_t ev = EventWord(0);
      ev.setNumOperands(2);
      ev.setThreadID(0xFF);
      ev.setNWIDbits(i);
      eventoperands_t eops(&ev, &op0);
      networkid_t nwid = NetworkID(i);
      rt.pushEventOperands(nwid, eops);
  }
  
  rt.simulate();
  
  printf("Check for termination now\n");
  
  bool status;
    // Check if all lanes are done
  while(1){
      status = true;
      for(int i = 0; i < num_lanes; i++){
          uint64_t val;
          rt.ud2t_memcpy(&val, 8, NetworkID(i), 0);
          status = status && (val == 1);
      }
      if(status)
          break;
  }
  printf("Total Sim Cycles :%ld\n", rt.getCurTick());
  printf("Test Success\n");
}
