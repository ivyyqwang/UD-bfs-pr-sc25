#include "transition.hh"
#include "archstate.hh"
#include "lanetypes.hh"
#include "debug.hh"

namespace basim {

/* basicTX Transition */
Cycles exeTransbasicTX(ArchState& ast, EncInst inst) {
  BASIM_WARNING("TRANSITION basicTX EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmTransbasicTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstBasictxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstBasictxTarget(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstBasictxSignature(inst));
  return disasm_str;
}

EncInst constrTransbasicTX(TransitionType type, int64_t attach, int64_t target, uint64_t signature) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstBasictxAttach(inst, attach);
  embdInstBasictxTarget(inst, target);
  embdInstBasictxSignature(inst, signature);
  return inst;
}

/* majorityTX Transition */
Cycles exeTransmajorityTX(ArchState& ast, EncInst inst) {
  BASIM_WARNING("TRANSITION majorityTX EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmTransmajorityTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMajoritytxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstMajoritytxTarget(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstMajoritytxSignature(inst));
  return disasm_str;
}

EncInst constrTransmajorityTX(TransitionType type, int64_t attach, int64_t target, uint64_t signature) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstMajoritytxAttach(inst, attach);
  embdInstMajoritytxTarget(inst, target);
  embdInstMajoritytxSignature(inst, signature);
  return inst;
}

/* defaultTX Transition */
Cycles exeTransdefaultTX(ArchState& ast, EncInst inst) {
  BASIM_WARNING("TRANSITION defaultTX EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmTransdefaultTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstDefaulttxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstDefaulttxTarget(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstDefaulttxSignature(inst));
  return disasm_str;
}

EncInst constrTransdefaultTX(TransitionType type, int64_t attach, int64_t target, uint64_t signature) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstDefaulttxAttach(inst, attach);
  embdInstDefaulttxTarget(inst, target);
  embdInstDefaulttxSignature(inst, signature);
  return inst;
}

/* epsilonTX Transition */
Cycles exeTransepsilonTX(ArchState& ast, EncInst inst) {
  BASIM_WARNING("TRANSITION epsilonTX EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmTransepsilonTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstEpsilontxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstEpsilontxTarget(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstEpsilontxSignature(inst));
  return disasm_str;
}

EncInst constrTransepsilonTX(TransitionType type, int64_t attach, int64_t target, uint64_t signature) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstEpsilontxAttach(inst, attach);
  embdInstEpsilontxTarget(inst, target);
  embdInstEpsilontxSignature(inst, signature);
  return inst;
}

/* commonTX Transition */
Cycles exeTranscommonTX(ArchState& ast, EncInst inst) {
  BASIM_WARNING("TRANSITION commonTX EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmTranscommonTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstCommontxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstCommontxTarget(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstCommontxSignature(inst));
  return disasm_str;
}

EncInst constrTranscommonTX(TransitionType type, int64_t attach, int64_t target, uint64_t signature) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstCommontxAttach(inst, attach);
  embdInstCommontxTarget(inst, target);
  embdInstCommontxSignature(inst, signature);
  return inst;
}

/* flaggedTX Transition */
Cycles exeTransflaggedTX(ArchState& ast, EncInst inst) {
  BASIM_WARNING("TRANSITION flaggedTX EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmTransflaggedTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstFlaggedtxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstFlaggedtxTarget(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstFlaggedtxSignature(inst));
  return disasm_str;
}

EncInst constrTransflaggedTX(TransitionType type, int64_t attach, int64_t target, uint64_t signature) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstFlaggedtxAttach(inst, attach);
  embdInstFlaggedtxTarget(inst, target);
  embdInstFlaggedtxSignature(inst, signature);
  return inst;
}

/* refillTX Transition */
Cycles exeTransrefillTX(ArchState& ast, EncInst inst) {
  BASIM_WARNING("TRANSITION refillTX EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmTransrefillTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstRefilltxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstRefilltxTarget(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstRefilltxSignature(inst));
  return disasm_str;
}

EncInst constrTransrefillTX(TransitionType type, int64_t attach, int64_t target, uint64_t signature) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstRefilltxAttach(inst, attach);
  embdInstRefilltxTarget(inst, target);
  embdInstRefilltxSignature(inst, signature);
  return inst;
}

/* eventTX Transition */
Cycles exeTranseventTX(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  if(*ast.lanestate == LaneState::NULLSTATE){
    // Current transition is an event transition
    // Work with event label
    *ast.lanestate = LaneState::EVENT_ACTION;
  }
  ast.uip += (extrInstEventtrAttach(inst) << 2); // Change this to reflect uip + attach
 
  lnstats->tran_count_event++;
  return Cycles(1);
}

std::string disasmTranseventTX(EncInst inst) {
  std::string disasm_str;
  disasm_str += "TRANS";
  disasm_str += std::string(" ") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstEventtxAttach(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstEventtxTarget(inst));
  return disasm_str;
}

EncInst constrTranseventTX(TransitionType type, int64_t attach, int64_t target) {
  EncInst inst;
  embdTransType(inst, type);
  embdInstEventtxAttach(inst, attach);
  embdInstEventtxTarget(inst, target);
  return inst;
}


}; // namespace basim
