#include "fp_arith_inst.hh"
#include "archstate.hh"
#include "lanetypes.hh" 
#include "debug.hh"
#include <cmath>
#include <cfenv>
#include "isa_cycles.hh"

namespace basim {

static inline double FP64ToDouble(uint64_t var) {
  return *reinterpret_cast<double *>(&var);
}

static inline float FP32ToFloat(uint32_t var) {
  return *reinterpret_cast<float *>(&var);
}

static inline float BF16ToFloat(uint16_t var) {
  uint32_t var32 = static_cast<uint32_t>(var) << 16;
  return *reinterpret_cast<float *>(&var32);
}

static inline uint64_t doubleToFP64(double var) {
  return *reinterpret_cast<uint64_t *>(&var);
}

static inline uint32_t floatToFP32(float var) {
  return *reinterpret_cast<uint32_t *>(&var);
}

static inline uint16_t floatToBF16(float var) {
  return static_cast<uint16_t>(*reinterpret_cast<uint32_t *>(&var) >> 16);
}

static inline uint64_t packTo64(uint32_t var_h, uint32_t var_l) {
  return (static_cast<uint64_t>(var_h) << 32) | static_cast<uint64_t>(var_l);
}

static uint64_t getFPArithStatus(uint64_t FSCR) {
  if (std::fetestexcept(FE_INVALID))    FSCR |= 0x8000000000000000;
  if (std::fetestexcept(FE_DIVBYZERO))  FSCR |= 0x4000000000000000;
  if (std::fetestexcept(FE_OVERFLOW))   FSCR |= 0x2000000000000000;
  if (std::fetestexcept(FE_UNDERFLOW))  FSCR |= 0x1000000000000000;
  if (std::fetestexcept(FE_INEXACT))    FSCR |= 0x0800000000000000;

  return FSCR;
}

static uint64_t getBF16ArithStatus(float val, uint16_t bf16_val, uint64_t FSCR) {
  // Overflow, infinite value
  if ((bf16_val & 0x7F80) == 0x7F80 && (bf16_val & 0x007F) == 0)
    FSCR |= 0x2000000000000000;
  // Underflow
  if (val != 0 && (bf16_val & 0x7FFF) == 0)  FSCR |= 0x1000000000000000;
  if ((bf16_val & 0x7F80) != 0x7F80 && BF16ToFloat(bf16_val) != val)  
    FSCR |= 0x0800000000000000;

  return FSCR;
}

/* fmadd.64, fadd.64, fsub.64, fmul.64, fdiv.64, fsqrt.64, fexp.64, fmadd.32, fadd.32, fsub.32, fmul.32, fdiv.32, fsqrt.32, fexp.32, fmadd.b16, fadd.b16, fsub.b16, fmul.b16, fdiv.b16, fsqrt.b16, fexp.b16 Instruction */
Cycles exeInstFmaddFaddFsubFmulFdivFsqrtFexp(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  uint64_t FSCR = tst->readReg(RegId::X4) & 0x07FFFFFFFFFFFFFF;
  double xs_dbl_data, xt_dbl_data, xd_dbl_data, dbl_result;
  float xs_sgl_data, xt_sgl_data, xd_sgl_data, sgl_result;

  switch (extrInstFadd_64Precision(inst))
  {
  case 1: // 64-bit
    switch (extrInstFadd_64Func(inst)) {
    case 0:
      xs_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFmadd_64Xs(inst))));
      xt_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFmadd_64Xt(inst))));
      xd_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFmadd_64Xd(inst))));

      std::feclearexcept(FE_ALL_EXCEPT);
      dbl_result = xd_dbl_data + xs_dbl_data * xt_dbl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFmadd_64Xd(inst), doubleToFP64(dbl_result));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FMADD_64)]++;
#endif
      return Cycles(FP_ARITH_MUL_CYCLES); // TODO: figure out the correct number of cycles
    
    case 1:
      xs_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFadd_64Xs(inst))));
      xt_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFadd_64Xt(inst))));

      std::feclearexcept(FE_ALL_EXCEPT);
      dbl_result = xs_dbl_data + xt_dbl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFadd_64Xd(inst), doubleToFP64(dbl_result));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FADD_64)]++;
#endif
      return Cycles(FP_ARITH_ADDSUB_CYCLES); // TODO: figure out the correct number of cycles
    
    case 2:
      xs_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFsub_64Xs(inst))));
      xt_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFsub_64Xt(inst))));

      std::feclearexcept(FE_ALL_EXCEPT);
      dbl_result = xs_dbl_data - xt_dbl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFsub_64Xd(inst), doubleToFP64(dbl_result));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FSUB_64)]++;
#endif
      return Cycles(FP_ARITH_ADDSUB_CYCLES); // TODO: figure out the correct number of cycles

    case 3:
      xs_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFmul_64Xs(inst))));
      xt_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFmul_64Xt(inst))));

      std::feclearexcept(FE_ALL_EXCEPT);
      dbl_result = xs_dbl_data * xt_dbl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFmul_64Xd(inst), doubleToFP64(dbl_result));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FMUL_64)]++;
#endif
      return Cycles(FP_ARITH_MUL_CYCLES); // TODO: figure out the correct number of cycles
    
    
    case 4:
      xs_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFdiv_64Xs(inst))));
      xt_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFdiv_64Xt(inst))));
      
      std::feclearexcept(FE_ALL_EXCEPT);
      dbl_result = xs_dbl_data / xt_dbl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFdiv_64Xd(inst), doubleToFP64(dbl_result));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FDIV_64)]++;
#endif
      return Cycles(FP_ARITH_DIVMOD_CYCLES); // TODO: figure out the correct number of cycles

    case 5:
      xs_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFsqrt_64Xs(inst))));

      std::feclearexcept(FE_ALL_EXCEPT);
      dbl_result = std::sqrt(xs_dbl_data);

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFsqrt_64Xd(inst), doubleToFP64(dbl_result));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FSQRT_64)]++;
#endif
      return Cycles(FP_ARITH_EXPSQRT_CYCLES); // TODO: figure out the correct number of cycles
    
    case 6:
      xs_dbl_data = FP64ToDouble(static_cast<uint64_t>(tst->readReg(extrInstFexp_64Xs(inst))));

      std::feclearexcept(FE_ALL_EXCEPT);
      dbl_result = std::exp(xs_dbl_data);

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFexp_64Xd(inst), doubleToFP64(dbl_result));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FEXP_64)]++;
#endif
      return Cycles(FP_ARITH_EXPSQRT_CYCLES); // TODO: figure out the correct number of cycles

    default:
      BASIM_ERROR("EXECUTING fmadd.64, fadd.64, fsub.64, fmul.64, fdiv.64, fsqrt.64, fexp.64 WITH UNKNOWN FUNC");
      return Cycles(0);
    }
    break;

  case 2: // 32-bit
    switch (extrInstFadd_64Func(inst)) {
    case 0:
      xs_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFmadd_32Xs(inst)) & 0xFFFFFFFF));
      xt_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFmadd_32Xt(inst)) & 0xFFFFFFFF));
      xd_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFmadd_32Xd(inst)) & 0xFFFFFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xd_sgl_data + xs_sgl_data * xt_sgl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFmadd_32Xd(inst), static_cast<uint64_t>(floatToFP32(sgl_result)));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FMADD_32)]++;
#endif
      return Cycles(FP_ARITH_MUL_CYCLES); 
    
    case 1:
      xs_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFadd_32Xs(inst)) & 0xFFFFFFFF));
      xt_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFadd_32Xt(inst)) & 0xFFFFFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data + xt_sgl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFadd_32Xd(inst), static_cast<uint64_t>(floatToFP32(sgl_result)));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FADD_32)]++;
#endif
      return Cycles(FP_ARITH_ADDSUB_CYCLES); 
    
    case 2:
      xs_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFsub_32Xs(inst)) & 0xFFFFFFFF));
      xt_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFsub_32Xt(inst)) & 0xFFFFFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data - xt_sgl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFsub_32Xd(inst), static_cast<uint64_t>(floatToFP32(sgl_result)));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FSUB_32)]++;
#endif
      return Cycles(FP_ARITH_ADDSUB_CYCLES); 

    case 3:
      xs_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFmul_32Xs(inst)) & 0xFFFFFFFF));
      xt_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFmul_32Xt(inst)) & 0xFFFFFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data * xt_sgl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFmul_32Xd(inst), static_cast<uint64_t>(floatToFP32(sgl_result)));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FMUL_32)]++;
#endif
      return Cycles(FP_ARITH_MUL_CYCLES); 
    
    case 4:
      xs_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFdiv_32Xs(inst)) & 0xFFFFFFFF));
      xt_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFdiv_32Xt(inst)) & 0xFFFFFFFF));
      
      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data / xt_sgl_data;

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFdiv_32Xd(inst), static_cast<uint64_t>(floatToFP32(sgl_result)));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FDIV_32)]++;
#endif
      return Cycles(FP_ARITH_DIVMOD_CYCLES); 

    case 5:
      xs_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFsqrt_32Xs(inst)) & 0xFFFFFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = std::sqrt(xs_sgl_data);

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFsqrt_32Xd(inst), static_cast<uint64_t>(floatToFP32(sgl_result)));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FSQRT_32)]++;
#endif
      return Cycles(FP_ARITH_EXPSQRT_CYCLES);
    
    case 6:
      xs_sgl_data = FP32ToFloat(static_cast<uint32_t>(tst->readReg(extrInstFexp_32Xs(inst)) & 0xFFFFFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = std::exp(xs_sgl_data);

      tst->writeReg(RegId::X4, getFPArithStatus(FSCR));
      tst->writeReg(extrInstFexp_32Xd(inst), static_cast<uint64_t>(floatToFP32(sgl_result)));
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FEXP_32)]++;
#endif
      return Cycles(FP_ARITH_EXPSQRT_CYCLES);

    default:
      BASIM_ERROR("EXECUTING fmadd.32, fadd.32, fsub.32, fmul.32, fdiv.32, fsqrt.32, fexp.32 WITH UNKNOWN FUNC");
      return Cycles(0);
    }
    break;

  case 3: // bfloat16
    uint16_t bf16_result;
    switch (extrInstFadd_64Func(inst)) {
    case 0:
      xs_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFmadd_b16Xs(inst)) & 0xFFFF));
      xt_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFmadd_b16Xt(inst)) & 0xFFFF));
      xd_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFmadd_b16Xd(inst)) & 0xFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xd_sgl_data + xs_sgl_data * xt_sgl_data;

      bf16_result = floatToBF16(sgl_result);
      tst->writeReg(RegId::X4, getBF16ArithStatus(sgl_result, bf16_result, getFPArithStatus(FSCR)));
      tst->writeReg(extrInstFmadd_b16Xd(inst), bf16_result);
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FMADD_B16)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    
    case 1:
      xs_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFadd_b16Xs(inst)) & 0xFFFF));
      xt_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFadd_b16Xt(inst)) & 0xFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data + xt_sgl_data;

      bf16_result = floatToBF16(sgl_result);
      tst->writeReg(RegId::X4, getBF16ArithStatus(sgl_result, bf16_result, getFPArithStatus(FSCR)));
      tst->writeReg(extrInstFadd_b16Xd(inst), bf16_result);
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FADD_B16)]++;
#endif
      return Cycles(FP_ARITH_ADDSUB_CYCLES); 
    
    case 2:
      xs_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFsub_b16Xs(inst)) & 0xFFFF));
      xt_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFsub_b16Xt(inst)) & 0xFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data - xt_sgl_data;

      bf16_result = floatToBF16(sgl_result);
      tst->writeReg(RegId::X4, getBF16ArithStatus(sgl_result, bf16_result, getFPArithStatus(FSCR)));
      tst->writeReg(extrInstFsub_b16Xd(inst), bf16_result);
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FSUB_B16)]++;
#endif
      return Cycles(FP_ARITH_ADDSUB_CYCLES); 

    case 3:
      xs_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFmul_b16Xs(inst)) & 0xFFFF));
      xt_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFmul_b16Xt(inst)) & 0xFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data * xt_sgl_data;

      bf16_result = floatToBF16(sgl_result);
      tst->writeReg(RegId::X4, getBF16ArithStatus(sgl_result, bf16_result, getFPArithStatus(FSCR)));
      tst->writeReg(extrInstFmul_b16Xd(inst), bf16_result);
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FMUL_B16)]++;
#endif
      return Cycles(FP_ARITH_MUL_CYCLES); 
    
    case 4:
      xs_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFdiv_b16Xs(inst)) & 0xFFFF));
      xt_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFdiv_b16Xt(inst)) & 0xFFFF));
      
      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = xs_sgl_data / xt_sgl_data;

      bf16_result = floatToBF16(sgl_result);
      tst->writeReg(RegId::X4, getBF16ArithStatus(sgl_result, bf16_result, getFPArithStatus(FSCR)));
      tst->writeReg(extrInstFdiv_b16Xd(inst), bf16_result);
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FDIV_B16)]++;
#endif
      return Cycles(FP_ARITH_DIVMOD_CYCLES); 

    case 5:
      xs_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFsqrt_b16Xs(inst)) & 0xFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = std::sqrt(xs_sgl_data);

      bf16_result = floatToBF16(sgl_result);
      tst->writeReg(RegId::X4, getBF16ArithStatus(sgl_result, bf16_result, getFPArithStatus(FSCR)));
      tst->writeReg(extrInstFsqrt_b16Xd(inst), bf16_result);
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FSQRT_B16)]++;
#endif
      return Cycles(FP_ARITH_EXPSQRT_CYCLES);
    
    case 6:
      xs_sgl_data = BF16ToFloat(static_cast<uint16_t>(tst->readReg(extrInstFexp_b16Xs(inst)) & 0xFFFF));

      std::feclearexcept(FE_ALL_EXCEPT);
      sgl_result = std::exp(xs_sgl_data);

      bf16_result = floatToBF16(sgl_result);
      tst->writeReg(RegId::X4, getBF16ArithStatus(sgl_result, bf16_result, getFPArithStatus(FSCR)));
      tst->writeReg(extrInstFexp_b16Xd(inst), bf16_result);
      ast.uip += 4;
      lnstats->inst_count_fparith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FEXP_B16)]++;
#endif
      return Cycles(FP_ARITH_EXPSQRT_CYCLES);

    default:
      BASIM_ERROR("EXECUTING fmadd.b16, fadd.b16, fsub.b16, fmul.b16, fdiv.b16, fsqrt.b16, fexp.b16 WITH UNKNOWN FUNC");
      return Cycles(0);
    }
  
  default:
    BASIM_ERROR("EXECUTING fmadd.64, fadd.64, fsub.64, fmul.64, fdiv.64, fsqrt.64, fexp.64, fmadd.32, fadd.32, fsub.32, fmul.32, fdiv.32, fsqrt.32, fexp.32, fmadd.b16, fadd.b16, fsub.b16, fmul.b16, fdiv.b16, fsqrt.b16, fexp.b16 WITH UNKNOWN PRECISION");
    return Cycles(0);
  }
  
  return Cycles(0);
}

std::string disasmInstFmaddFaddFsubFmulFdivFsqrtFexp(EncInst inst) {
  std::string disasm_str;
  switch (extrInstFadd_64Precision(inst))
  {
  case 1: // 64-bit
    switch (extrInstFadd_64Func(inst)) {
    case 0:
      disasm_str += "FMADD.64";
      break;
    case 1:
      disasm_str += "FADD.64";
      break;
    case 2:
      disasm_str += "FSUB.64";
      break;
    case 3:
      disasm_str += "FMUL.64";
      break;
    case 4:
      disasm_str += "FDIV.64";
      break;
    case 5:
      disasm_str += "FSQRT.64";
      break;
    case 6:
      disasm_str += "FEXP.64";
      break;
    default:
      BASIM_ERROR("DISASM fmadd.64, fadd.64, fsub.64, fmul.64, fdiv.64, fsqrt.64, fexp.64 WITH UNKNOWN FUNC");
    }
    break;
  case 2: // 32-bit
    switch (extrInstFadd_64Func(inst)) {
    case 0:
      disasm_str += "FMADD.32";
      break;
    case 1:
      disasm_str += "FADD.32";
      break;
    case 2:
      disasm_str += "FSUB.32";
      break;
    case 3:
      disasm_str += "FMUL.32";
      break;
    case 4:
      disasm_str += "FDIV.32";
      break;
    case 5:
      disasm_str += "FSQRT.32";
      break;
    case 6:
      disasm_str += "FEXP.32";
      break;
    default:
      BASIM_ERROR("DISASM fmadd.32, fadd.32, fsub.32, fmul.32, fdiv.32, fsqrt.32, fexp.32 WITH UNKNOWN FUNC");
    }
    break;
  case 3: // bfloat16
    switch (extrInstFadd_64Func(inst)) {
    case 0:
      disasm_str += "FMADD.B16";
      break;
    case 1:
      disasm_str += "FADD.B16";
      break;
    case 2:
      disasm_str += "FSUB.B16";
      break;
    case 3:
      disasm_str += "FMUL.B16";
      break;
    case 4:
      disasm_str += "FDIV.B16";
      break;
    case 5:
      disasm_str += "FSQRT.B16";
      break;
    case 6:
      disasm_str += "FEXP.B16";
      break;
    default:
      BASIM_ERROR("DISASM fmadd.b16, fadd.b16, fsub.b16, fmul.b16, fdiv.b16, fsqrt.b16, fexp.b16 WITH UNKNOWN FUNC");
    }
    break;
  default:
    BASIM_ERROR("DISASM fmadd.64, fadd.64, fsub.64, fmul.64, fdiv.64, fsqrt.64, fexp.64, fmadd.32, fadd.32, fsub.32, fmul.32, fdiv.32, fsqrt.32, fexp.32, fmadd.b16, fadd.b16, fsub.b16, fmul.b16, fdiv.b16, fsqrt.b16, fexp.b16 WITH UNKNOWN PRECISION");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstFmadd_64Xs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstFmadd_64Xt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstFmadd_64Xd(inst))];
  return disasm_str;
}

EncInst constrInstFmaddFaddFsubFmulFdivFsqrtFexp(uint64_t func, uint64_t precision, RegId Xs, RegId Xt, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::FMADD_64);
  embdInstFmadd_64Func(inst, func);
  embdInstFmadd_64Precision(inst, precision);
  embdInstFmadd_64Xs(inst, Xs);
  embdInstFmadd_64Xt(inst, Xt);
  embdInstFmadd_64Xd(inst, Xd);
  return inst;
}


/* fcnvt.64.i64, fcnvt.32.i32, fcnvt.i64.64, fcnvt.i32.32, fcnvt.64.32, fcnvt.64.b16, fcnvt.32.64, fcnvt.32.b16, fcnvt.b16.64, fcnvt.b16.32 Instruction */
Cycles exeInstFcnvt(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;

  // [000]-RNE: Round to the nearest, ties to even
  // [001]-RTZ: Round toward zero
  // [010]-RDN: Round down - toward negative infinity
  // [100]-RMM: Round to Nearest, ties to max magnitude 

  // NV: Invalid operation
  // DZ: Divide by zero / NaN
  // OF: Overflow
  // UF: Underflow
  // NX: Inexact

  uint64_t nv = 0;
  uint64_t dz = 0;
  uint64_t of = 0;
  uint64_t uf = 0;
  uint64_t nx = 0;
  
  uint64_t rm = (0x0700000000000000 & tst->readReg(RegId::X4)) >> 56;

  regval_t xs = tst->readReg(extrInstFcnvt_64_i64Xs(inst));
  regval_t old_xs = xs;
  
  switch ((extrInstFcnvt_64_i64Precision(inst) << 3) | extrInstFcnvt_64_i64Func(inst)) {
    case 8: {
      // fcnvt.64.i64  Xs, Xd
      int64_t result = *reinterpret_cast<double *>(&xs);
      double t_xs = result;
      xs = static_cast<uint64_t>(result);

      if (doubleToFP64(t_xs) != old_xs) {
        nx = 1;
        if (xs == 0x8000000000000000) {
          of = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_64_I64)]++;
#endif

      break;
    }
    case 16: {
      // fcnvt.32.i32  Xs, Xd
      int32_t result = *reinterpret_cast<float *>(&xs);
      float t_xs = result;
      xs = static_cast<uint32_t>(result);

      if (floatToFP32(t_xs) != (old_xs & 0x00000000FFFFFFFF)) {
        nx = 1;
        if (xs == 0x0000000080000000) {
          of = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_32_I32)]++;
#endif

      break;
    }
    case 48: {
      // fcnvt.i64.64  Xs, Xd
      double result = static_cast<int64_t>(xs);
      int64_t t_xs = result;
      xs = doubleToFP64(result);

      if ((xs & 0x7FF0000000000000) == 0x7FF0000000000000) {
        nx = 1;
        if (xs & 0x000FFFFFFFFFFFFF) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (static_cast<uint64_t>(t_xs) != old_xs) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_I64_64)]++;
#endif

      break;
    }
    case 56: {
      // fcnvt.i32.32  Xs, Xd
      float result = static_cast<int32_t>(xs & 0x00000000FFFFFFFF);
      int32_t t_xs = result;
      xs = floatToFP32(result);

      if ((xs & 0x000000007F800000) == 0x000000007F800000) {
        nx = 1;
        if (xs & 0x00000000007FFFFF) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (static_cast<uint32_t>(t_xs) != (old_xs & 0x00000000FFFFFFFF)) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_I32_32)]++;
#endif

      break;
    }
    case 9: {
      // fcnvt.64.32 Xs, Xd
      float result = *reinterpret_cast<double *>(&xs);
      double t_xs = result;
      xs = floatToFP32(result);

      if ((xs & 0x000000007F800000) == 0x000000007F800000) {
        nx = 1;
        if (xs & 0x00000000007FFFFF) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (doubleToFP64(t_xs) != old_xs) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_64_32)]++;
#endif

      break;
    }
    case 10: {
      // fcnvt.64.b16 Xs, Xd
      float result = BF16ToFloat(floatToBF16(*reinterpret_cast<double *>(&xs)));
      double t_xs = result;
      xs = floatToBF16(result);

      if ((xs & 0x0000000000007F80) == 0x0000000000007F80) {
        nx = 1;
        if (xs & 0x000000000000007F) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (doubleToFP64(t_xs) != old_xs) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_64_B16)]++;
#endif

      break;
    }
    case 17: {
      // fcnvt.32.64 Xs, Xd
      double result = *reinterpret_cast<float *>(&xs);
      float t_xs = result;
      xs = doubleToFP64(result);

      if ((xs & 0x7FF0000000000000) == 0x7FF0000000000000) {
        nx = 1;
        if (xs & 0x000FFFFFFFFFFFFF) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (floatToFP32(t_xs) != (old_xs & 0x00000000FFFFFFFF)) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_32_64)]++;
#endif

      break;
    }
    case 18: {
      // fcnvt.32.b16 Xs, Xd
      float result = BF16ToFloat(floatToBF16(*reinterpret_cast<float *>(&xs)));
      float t_xs = result;
      xs = floatToBF16(result);

      if ((xs & 0x0000000000007F80) == 0x0000000000007F80) {
        nx = 1;
        if (xs & 0x000000000000007F) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (floatToFP32(t_xs) != (old_xs & 0x00000000FFFFFFFF)) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_32_B16)]++;
#endif

      break;
    }
    case 25: {
      // fcnvt.b16.64 Xs, Xd
      double result = BF16ToFloat(xs);
      float t_xs = result;
      xs = doubleToFP64(result);

      if ((xs & 0x7FF0000000000000) == 0x7FF0000000000000) {
        nx = 1;
        if (xs & 0x000FFFFFFFFFFFFF) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (floatToBF16(t_xs) != (old_xs & 0x000000000000FFFF)) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_B16_64)]++;
#endif
      
      break;
    }
    case 26: {
      // fcnvt.b16.32 Xs, Xd
      float result = BF16ToFloat(xs);
      float t_xs = result;
      xs = floatToFP32(result);

      if ((xs & 0x000000007F800000) == 0x000000007F800000) {
        nx = 1;
        if (xs & 0x00000000007FFFFF) {
          dz = 1;
        } else {
          of = 1;
        }
      } else if (floatToBF16(t_xs) != (old_xs & 0x000000000000FFFF)) {
        nx = 1;
        if (result == 0) {
          uf = 1;
        }
      }
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FCNVT_B16_32)]++;
#endif

      break;
    }
    default: {
      nv = 1;
      BASIM_WARNING("EXECUTING fcnvt.64.i64, fcnvt.32.i32, fcnvt.i64.64, fcnvt.i32.32, fcnvt.64.32, fcnvt.64.b16, fcnvt.32.64, fcnvt.32.b16, fcnvt.b16.64, fcnvt.b16.32 WITH UNKNOWN FUNC OR PRECISION");
      break;
    }
  }
  nv <<= 63;
  dz <<= 62;
  of <<= 61;
  uf <<= 60;
  nx <<= 59;
  rm <<= 56;
  
  uint64_t FSCR = tst->readReg(RegId::X4) & 0x07FFFFFFFFFFFFFF;
  tst->writeReg(RegId::X4, nv | dz | of | uf | nx | rm | FSCR);
  tst->writeReg(extrInstFcnvt_64_i64Xd(inst), xs);
    ast.uip += 4;
  lnstats->inst_count_fparith++;
  return Cycles(FCNVT_CYCLES);
}

std::string disasmInstFcnvt(EncInst inst) {
  std::string disasm_str;
  switch ((extrInstFcnvt_64_i64Precision(inst) << 3) | extrInstFcnvt_64_i64Func(inst)) {
  case 8:
    disasm_str += "FCNVT.64.I64";
    break;
  case 16:
    disasm_str += "FCNVT.32.I32";
    break;
  case 48:
    disasm_str += "FCNVT.I64.64";
    break;
  case 56:
    disasm_str += "FCNVT.I32.32";
    break;
  case 9:
    disasm_str += "FCNVT.64.32";
    break;
  case 10:
    disasm_str += "FCNVT.64.B16";
    break;
  case 17:
    disasm_str += "FCNVT.32.64";
    break;
  case 18:
    disasm_str += "FCNVT.32.B16";
    break;
  case 25:
    disasm_str += "FCNVT.B16.64";
    break;
  case 26:
    disasm_str += "FCNVT.B16.32";
    break;
  default:
    BASIM_WARNING("DISASM fcnvt.64.i64, fcnvt.32.i32, fcnvt.i64.64, fcnvt.i32.32, fcnvt.64.32, fcnvt.64.b16, fcnvt.32.64, fcnvt.32.b16, fcnvt.b16.64, fcnvt.b16.32 WITH UNKNOWN FUNC OR PRECISION");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstFcnvt_64_i64Xs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstFcnvt_64_i64Xd(inst))];
  return disasm_str;
}

EncInst constrInstFcnvt(uint64_t func, uint64_t precision, RegId Xs, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::FCNVT_64_I64);
  embdInstFcnvt_64_i64Func(inst, func);
  embdInstFcnvt_64_i64Precision(inst, precision);
  embdInstFcnvt_64_i64Xs(inst, Xs);
  embdInstFcnvt_64_i64Xd(inst, Xd);
  return inst;
}


}; // namespace basim
