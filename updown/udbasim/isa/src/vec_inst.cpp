#include "vec_inst.hh"
#include "archstate.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include "debug.hh"
#include <cmath>
#include <cfenv>

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

static inline uint64_t packTo64(uint32_t vars[]) {
  return (static_cast<uint64_t>(vars[1]) << 32) | static_cast<uint64_t>(vars[0]);
}

static inline uint64_t packTo64(uint16_t vars[]) {
  return (static_cast<uint64_t>(vars[3]) << 48) | (static_cast<uint64_t>(vars[2]) << 32) | (static_cast<uint64_t>(vars[1]) << 16) | static_cast<uint64_t>(vars[0]);
}

void setFPArithStatus(uint64_t &FSCR) {
  if (std::fetestexcept(FE_INVALID))    FSCR |= 0x8000000000000000;
  if (std::fetestexcept(FE_DIVBYZERO))  FSCR |= 0x4000000000000000;
  if (std::fetestexcept(FE_OVERFLOW))   FSCR |= 0x2000000000000000;
  if (std::fetestexcept(FE_UNDERFLOW))  FSCR |= 0x1000000000000000;
  if (std::fetestexcept(FE_INEXACT))    FSCR |= 0x0800000000000000;

  return ;
}

void setBF16ArithStatus(float val, uint16_t bf16_val, uint64_t &FSCR) {
  // Overflow, infinite value
  if ((bf16_val & 0x7F80) == 0x7F80 && (bf16_val & 0x007F) == 0)
    FSCR |= 0x2000000000000000;
  // Underflow
  if (val != 0 && (bf16_val & 0x7FFF) == 0)  FSCR |= 0x1000000000000000;
  // Inexact
  if ((bf16_val & 0x7F80) != 0x7F80 && BF16ToFloat(bf16_val) != val)  
    FSCR |= 0x0800000000000000;  return;
}


/* vmadd.32, vadd.32, vsub.32, vmul.32, vdiv.32, vsqrt.32, vexp.32, vmadd.b16, vadd.b16, vsub.b16, vmul.b16, vdiv.b16, vsqrt.b16, vexp.b16, vmadd.i32, vadd.i32, vsub.i32, vmul.i32, vdiv.i32, vsqrt.i32, vexp.i32 Instruction */
Cycles exeInstVmaddVaddVsubVmulVdivVsqrtVexp(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  uint64_t FSCR = tst->readReg(RegId::X4)& 0x07FFFFFFFFFFFFFF;
  uint64_t mask = extrInstVmadd_32Mask(inst);
  uint64_t xs_vdata, xt_vdata, xd_vdata, vresult;
  float xs_data, xt_data, xd_data, result;
  int32_t xs_idata, xt_idata, xd_idata, iresult;

  xs_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmadd_32Xs(inst)));
  xd_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmadd_32Xd(inst)));
  switch (extrInstVmadd_32Precision(inst))
  {
  case 2: // 32-bit
    uint32_t fp32_result[2];
    switch (extrInstVmadd_32Func(inst)) {
    case 0:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmadd_32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = FP32ToFloat(static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF));
          xt_data = FP32ToFloat(static_cast<uint32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF));
          xd_data = FP32ToFloat(static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xd_data + xs_data * xt_data;

          setFPArithStatus(FSCR);
          fp32_result[i] = floatToFP32(result);
        } else {
          fp32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVmadd_32Xd(inst), packTo64(fp32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VMADD_32)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    
    case 1:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVadd_32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = FP32ToFloat(static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF));
          xt_data = FP32ToFloat(static_cast<uint32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data + xt_data;

          setFPArithStatus(FSCR);
          fp32_result[i] = floatToFP32(result);
        } else {
          fp32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVadd_32Xd(inst), packTo64(fp32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VADD_32)]++;
#endif
      return Cycles(1); 
    
    case 2:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVsub_32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = FP32ToFloat(static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF));
          xt_data = FP32ToFloat(static_cast<uint32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data - xt_data;

          setFPArithStatus(FSCR);
          fp32_result[i] = floatToFP32(result);
        } else {
          fp32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVsub_32Xd(inst), packTo64(fp32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VSUB_32)]++;
#endif
      return Cycles(1); 

    case 3:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmul_32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = FP32ToFloat(static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF));
          xt_data = FP32ToFloat(static_cast<uint32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data * xt_data;

          setFPArithStatus(FSCR);
          fp32_result[i] = floatToFP32(result);
        } else {
          fp32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVmul_32Xd(inst), packTo64(fp32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VMUL_32)]++;
#endif
      return Cycles(1); 
    
    case 4:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVdiv_32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = FP32ToFloat(static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF));
          xt_data = FP32ToFloat(static_cast<uint32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data / xt_data;

          setFPArithStatus(FSCR);
          fp32_result[i] = floatToFP32(result);
        } else {
          fp32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVdiv_32Xd(inst), packTo64(fp32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VDIV_32)]++;
#endif
      return Cycles(1); 

    case 5:
      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = FP32ToFloat(static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = std::sqrt(xs_data);

          setFPArithStatus(FSCR);
          fp32_result[i] = floatToFP32(result);
        } else {
          fp32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVsqrt_32Xd(inst), packTo64(fp32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VSQRT_32)]++;
#endif
      return Cycles(1); 
    
    case 6:
      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = FP32ToFloat(static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = std::exp(xs_data);

          setFPArithStatus(FSCR);
          fp32_result[i] = floatToFP32(result);
        } else {
          fp32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVexp_32Xd(inst), packTo64(fp32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VEXP_32)]++;
#endif
      return Cycles(1); 

    default:
      BASIM_ERROR("EXECUTING vmadd.32, vadd.32, vsub.32, vmul.32, vdiv.32, vsqrt.32, vexp.32 WITH UNKNOWN FUNC");
      return Cycles(0);
    }
    break;

  case 3: // bfloat16
    uint16_t bf16_result[4];
    switch (extrInstFadd_64Func(inst)) {
    case 0:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmadd_b16Xt(inst)));

      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));
          xt_data = BF16ToFloat(static_cast<uint16_t>((xt_vdata >> (16 * i)) & 0xFFFF));
          xd_data = BF16ToFloat(static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xd_data + xs_data * xt_data;
          setFPArithStatus(FSCR);

          bf16_result[i] = floatToBF16(result);
          setBF16ArithStatus(result, bf16_result[i], FSCR);
        } else {
          bf16_result[i] = static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVmadd_b16Xd(inst), packTo64(bf16_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VMADD_B16)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    
    case 1:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVadd_b16Xt(inst)));

      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));
          xt_data = BF16ToFloat(static_cast<uint16_t>((xt_vdata >> (16 * i)) & 0xFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data + xt_data;
          setFPArithStatus(FSCR);

          bf16_result[i] = floatToBF16(result);
          setBF16ArithStatus(result, bf16_result[i], FSCR);
        } else {
          bf16_result[i] = static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVadd_b16Xd(inst), packTo64(bf16_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VADD_B16)]++;
#endif
      return Cycles(1); 
    
    case 2:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVsub_b16Xt(inst)));

      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));
          xt_data = BF16ToFloat(static_cast<uint16_t>((xt_vdata >> (16 * i)) & 0xFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data - xt_data;
          setFPArithStatus(FSCR);

          bf16_result[i] = floatToBF16(result);
          setBF16ArithStatus(result, bf16_result[i], FSCR);
        } else {
          bf16_result[i] = static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVsub_b16Xd(inst), packTo64(bf16_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VSUB_B16)]++;
#endif
      return Cycles(1); 

    case 3:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmul_b16Xt(inst)));

      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));
          xt_data = BF16ToFloat(static_cast<uint16_t>((xt_vdata >> (16 * i)) & 0xFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data * xt_data;
          setFPArithStatus(FSCR);

          bf16_result[i] = floatToBF16(result);
          setBF16ArithStatus(result, bf16_result[i], FSCR);
        } else {
          bf16_result[i] = static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVmul_b16Xd(inst), packTo64(bf16_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VMUL_B16)]++;
#endif
      return Cycles(1); 
    
    case 4:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVdiv_b16Xt(inst)));

      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));
          xt_data = BF16ToFloat(static_cast<uint16_t>((xt_vdata >> (16 * i)) & 0xFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = xs_data / xt_data;
          setFPArithStatus(FSCR);

          bf16_result[i] = floatToBF16(result);
          setBF16ArithStatus(result, bf16_result[i], FSCR);
        } else {
          bf16_result[i] = static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVdiv_b16Xd(inst), packTo64(bf16_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VDIV_B16)]++;
#endif
      return Cycles(1); 

    case 5:
      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = std::sqrt(xs_data);
          setFPArithStatus(FSCR);

          bf16_result[i] = floatToBF16(result);
          setBF16ArithStatus(result, bf16_result[i], FSCR);
        } else {
          bf16_result[i] = static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVsqrt_b16Xd(inst), packTo64(bf16_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VSQRT_B16)]++;
#endif
      return Cycles(1); 
    
    case 6:
      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          xs_data = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));

          std::feclearexcept(FE_ALL_EXCEPT);
          result = std::exp(xs_data);
          setFPArithStatus(FSCR);

          bf16_result[i] = floatToBF16(result);
          setBF16ArithStatus(result, bf16_result[i], FSCR);
        } else {
          bf16_result[i] = static_cast<uint16_t>((xd_vdata >> (16 * i)) & 0xFFFF);
        }
      }

      tst->writeReg(RegId::X4, FSCR);
      tst->writeReg(extrInstVexp_b16Xd(inst), packTo64(bf16_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VEXP_B16)]++;
#endif
      return Cycles(1); 

    default:
      BASIM_ERROR("EXECUTING vmadd.b16, vadd.b16, vsub.b16, vmul.b16, vdiv.b16, vsqrt.b16, vexp.b16 WITH UNKNOWN FUNC");
      return Cycles(0);
    }

  case 7: // 32-bit integer
    uint32_t i32_result[2];
    switch (extrInstVmadd_i32Func(inst)) {
    case 0:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmadd_i32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);
          xt_idata = static_cast<int32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF);
          xd_idata = static_cast<int32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);

          iresult = xd_idata + xs_idata * xt_idata;

          i32_result[i] = static_cast<uint32_t>(iresult); 
        } else {
          i32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(extrInstVmadd_32Xd(inst), packTo64(i32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VMADD_I32)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    
    case 1:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVadd_i32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);
          xt_idata = static_cast<int32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF);

          iresult = xs_idata + xt_idata;

          i32_result[i] = static_cast<uint32_t>(iresult); 
        } else {
          i32_result[i] = static_cast<int32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(extrInstVadd_32Xd(inst), packTo64(i32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VADD_I32)]++;
#endif
      return Cycles(1); 
    
    case 2:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVsub_i32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);
          xt_idata = static_cast<int32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF);

          iresult = xs_idata - xt_idata;

          i32_result[i] = static_cast<uint32_t>(iresult); 
        } else {
          i32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(extrInstVsub_32Xd(inst), packTo64(i32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VSUB_I32)]++;
#endif
      return Cycles(1); 

    case 3:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVmul_i32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);
          xt_idata = static_cast<int32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF);

          iresult = xs_idata * xt_idata;

          i32_result[i] = static_cast<uint32_t>(iresult); 
        } else {
          i32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(extrInstVmul_32Xd(inst), packTo64(i32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VMUL_I32)]++;
#endif
      return Cycles(1); 
    
    case 4:
      xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVdiv_i32Xt(inst)));

      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);
          xt_idata = static_cast<int32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF);

          iresult = xs_idata / xt_idata;

          i32_result[i] = static_cast<uint32_t>(iresult); 
        } else {
          i32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(extrInstVdiv_32Xd(inst), packTo64(i32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VDIV_I32)]++;
#endif
      return Cycles(1); 

    case 5:
      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);

          iresult = std::sqrt(xs_idata);

          i32_result[i] = static_cast<uint32_t>(iresult); 
        } else {
          i32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(extrInstVsqrt_32Xd(inst), packTo64(i32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VSQRT_I32)]++;
#endif
      return Cycles(1); 
    
    case 6:
      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);

          iresult = std::exp(xs_idata);

          i32_result[i] = static_cast<uint32_t>(iresult); 
        } else {
          i32_result[i] = static_cast<uint32_t>((xd_vdata >> (32 * i)) & 0xFFFFFFFF);
        }
      }

      tst->writeReg(extrInstVexp_32Xd(inst), packTo64(i32_result));
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VEXP_I32)]++;
#endif
      return Cycles(1); 

    default:
      BASIM_ERROR("EXECUTING vmadd.i32, vadd.i32, vsub.i32, vmul.i32, vdiv.i32, vsqrt.i32, vexp.i32 WITH UNKNOWN FUNC");
      return Cycles(0);
    }
    break;

  default:
    BASIM_ERROR("EXECUTING vmadd.32, vadd.32, vsub.32, vmul.32, vdiv.32, vsqrt.32, vexp.32, vmadd.b16, vadd.b16, vsub.b16, vmul.b16, vdiv.b16, vsqrt.b16, vexp.b16, vmadd.i32, vadd.i32, vsub.i32, vmul.i32, vdiv.i32, vsqrt.i32, vexp.i32 WITH UNKNOWN PRECISION");
    return Cycles(0);
  }
  return Cycles(0);
}

std::string disasmInstVmaddVaddVsubVmulVdivVsqrtVexp(EncInst inst) {
  std::string disasm_str;
  switch (extrInstVmadd_32Precision(inst))
  {
  case 2: // 32-bit
    switch (extrInstVmadd_32Func(inst)) {
    case 0:
      disasm_str += "VMADD.32";
      break;
    case 1:
      disasm_str += "VADD.32";
      break;
    case 2:
      disasm_str += "VSUB.32";
      break;
    case 3:
      disasm_str += "VMUL.32";
      break;
    case 4:
      disasm_str += "VDIV.32";
      break;
    case 5:
      disasm_str += "VSQRT.32";
      break;
    case 6:
      disasm_str += "VEXP.32";
      break;
    default:
      BASIM_ERROR("DISASM vmadd.32, vadd.32, vsub.32, vmul.32, vdiv.32, vsqrt.32, vexp.32 WITH UNKNOWN FUNC");
    }
    break;
  case 3: // bfloat16
    switch (extrInstVmadd_b16Func(inst)) {
    case 0:
      disasm_str += "VMADD.B16";
      break;
    case 1:
      disasm_str += "VADD.B16";
      break;
    case 2:
      disasm_str += "VSUB.B16";
      break;
    case 3:
      disasm_str += "VMUL.B16";
      break;
    case 4:
      disasm_str += "VDIV.B16";
      break;
    case 5:
      disasm_str += "VSQRT.B16";
      break;
    case 6:
      disasm_str += "VEXP.B16";
      break;
    default:
      BASIM_ERROR("DISASM vmadd.32, vadd.32, vsub.32, vmul.32, vdiv.32, vsqrt.32, vexp.32 WITH UNKNOWN FUNC");
    }
    break;
  case 7: // 32-bit integer
    switch (extrInstVmadd_i32Func(inst)) {
    case 0:
      disasm_str += "VMADD.I32";
      break;
    case 1:
      disasm_str += "VADD.I32";
      break;
    case 2:
      disasm_str += "VSUB.I32";
      break;
    case 3:
      disasm_str += "VMUL.I32";
      break;
    case 4:
      disasm_str += "VDIV.I32";
      break;
    case 5:
      disasm_str += "VSQRT.I32";
      break;
    case 6:
      disasm_str += "VEXP.I32";
      break;
    default:
      BASIM_ERROR("DISASM vmadd.32, vadd.32, vsub.32, vmul.32, vdiv.32, vsqrt.32, vexp.32 WITH UNKNOWN FUNC");
    }
    break;
  default:
    BASIM_ERROR("DISASM vmadd.32, vadd.32, vsub.32, vmul.32, vdiv.32, vsqrt.32, vexp.32, vmadd.b16, vadd.b16, vsub.b16, vmul.b16, vdiv.b16, vsqrt.b16, vexp.b16, vmadd.i32, vadd.i32, vsub.i32, vmul.i32, vdiv.i32, vsqrt.i32, vexp.i32 WITH UNKNOWN PRECISION");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstVmadd_32Xs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstVmadd_32Xt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstVmadd_32Xd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstVmadd_32Mask(inst));
  return disasm_str;
}

EncInst constrInstVmaddVaddVsubVmulVdivVsqrtVexp(uint64_t func, uint64_t precision, RegId Xs, RegId Xt, RegId Xd, uint64_t mask) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::VMADD_32);
  embdInstVmadd_32Func(inst, func);
  embdInstVmadd_32Precision(inst, precision);
  embdInstVmadd_32Xs(inst, Xs);
  embdInstVmadd_32Xt(inst, Xt);
  embdInstVmadd_32Xd(inst, Xd);
  embdInstVmadd_32Mask(inst, mask);
  return inst;
}


/* vgt.32, vgt.b16, vgt.i32 Instruction */
Cycles exeInstVgt(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
    uint64_t mask = extrInstVgt_32Mask(inst);
  uint64_t xs_vdata = static_cast<uint64_t>(tst->readReg(extrInstVgt_32Xs(inst)));
  uint64_t xt_vdata = static_cast<uint64_t>(tst->readReg(extrInstVgt_32Xt(inst)));
  uint64_t result = 0x0000000000000000;

  switch (extrInstVgt_32Precision(inst)) {
    case 2:
    {
      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          uint32_t xs_udata = static_cast<uint32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);
          uint32_t xt_udata = static_cast<uint32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF);
          float xs_idata = *reinterpret_cast<float *>(&xs_udata);
          float xt_idata = *reinterpret_cast<float *>(&xt_udata);
          result |= static_cast<uint64_t>(xs_idata > xt_idata) << i;
        }
      }
      result = (tst->readReg(extrInstVgt_32Xd(inst)) & (~mask)) | result;
      tst->writeReg(extrInstVexp_32Xd(inst), result);
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VGT_32)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    }
    case 3:
    {
      for (int i = 0; i < 4; i++) {
        if ((mask >> i) & 0x1) {
          float xs_idata = BF16ToFloat(static_cast<uint16_t>((xs_vdata >> (16 * i)) & 0xFFFF));
          float xt_idata = BF16ToFloat(static_cast<uint16_t>((xt_vdata >> (16 * i)) & 0xFFFF));
          result |= static_cast<uint64_t>(xs_idata > xt_idata) << i;
        }
      }
      result = (tst->readReg(extrInstVgt_32Xd(inst)) & (~mask)) | result;
      tst->writeReg(extrInstVexp_32Xd(inst), result);
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VGT_B16)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    }
    case 7:
    {
      for (int i = 0; i < 2; i++) {
        if ((mask >> i) & 0x1) {
          int xs_idata = static_cast<int32_t>((xs_vdata >> (32 * i)) & 0xFFFFFFFF);
          int xt_idata = static_cast<int32_t>((xt_vdata >> (32 * i)) & 0xFFFFFFFF);
          result |= static_cast<uint64_t>(xs_idata > xt_idata) << i;
        }
      }
      result = (tst->readReg(extrInstVgt_32Xd(inst)) & (~mask)) | result;
      tst->writeReg(extrInstVexp_32Xd(inst), result);
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VGT_I32)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    }
    default:
    {
      BASIM_ERROR("EXECUTING vgt.32, vgt.b16, vgt.i32 WITH UNKNOWN PRECISION");
      return Cycles(0);
    }
  }
}

std::string disasmInstVgt(EncInst inst) {
  std::string disasm_str;
  switch (extrInstVgt_32Precision(inst)) {
  case 2:
    disasm_str += "VGT.32";
    break;
  case 3:
    disasm_str += "VGT.B16";
    break;
  case 7:
    disasm_str += "VGT.I32";
    break;
  default:
    BASIM_ERROR("DISASM vgt.32, vgt.b16, vgt.i32 WITH UNKNOWN PRECISION");
    break;
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstVgt_32Xs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstVgt_32Xt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstVgt_32Xd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstVgt_32Mask(inst));
  return disasm_str;
}

EncInst constrInstVgt(uint64_t precision, RegId Xs, RegId Xt, RegId Xd, uint64_t mask) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::VGT_32);
  embdInstVgt_32Precision(inst, precision);
  embdInstVgt_32Xs(inst, Xs);
  embdInstVgt_32Xt(inst, Xt);
  embdInstVgt_32Xd(inst, Xd);
  embdInstVgt_32Mask(inst, mask);
  return inst;
}


/* vfill.32, vfill.i32, vfill.b16 Instruction */
Cycles exeInstVfill(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
    uint64_t mask = extrInstVgt_32Mask(inst);
  uint64_t imm_data = (extrInstVfill_32Immb(inst) << BF_VFILL_32_IMMA_NBITS) | extrInstVfill_32Imma(inst);
  uint64_t result = 0x0000000000000000;

  switch (extrInstVfill_32Precision(inst)) {
    case 2:
    {
      result = (imm_data << 48) | (imm_data << 16);
      tst->writeReg(extrInstVfill_32Xd(inst), result);
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VFILL_32)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    }
    case 3:
    {
      result = (imm_data << 48) | (imm_data << 32) | (imm_data << 16) | imm_data;
      tst->writeReg(extrInstVfill_32Xd(inst), result);
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VFILL_B16)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    }
    case 7:
    {
      if (imm_data & 0x0000000000008000) {
        imm_data |= 0x00000000FFFF0000;
      }
      result = (imm_data << 32) | imm_data;
      tst->writeReg(extrInstVfill_32Xd(inst), result);
      ast.uip += 4;
      lnstats->inst_count_vec++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::VFILL_I32)]++;
#endif
      return Cycles(1); // TODO: figure out the correct number of cycles
    }
    default:
    {
      BASIM_ERROR("EXECUTING vfill.32, vfill.b16, vfill.i32 WITH UNKNOWN PRECISION");
      return Cycles(0);
    }
  }
}

std::string disasmInstVfill(EncInst inst) {
  std::string disasm_str;
  switch (extrInstVfill_32Precision(inst)) {
  case 2:
    disasm_str += "VFILL.32";
    break;
  case 3:
    disasm_str += "VFILL.B16";
    break;
  case 7:
    disasm_str += "VFILL.I32";
    break;
  default:
    BASIM_ERROR("DISASM vfill.32, vfill.b16, vfill.i32 WITH UNKNOWN PRECISION");
    break;
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstVfill_32Xd(inst))];
  disasm_str += std::string(" ") + std::to_string((extrInstVfill_32Immb(inst) << BF_VFILL_32_IMMA_NBITS) | extrInstVfill_32Imma(inst));
  return disasm_str;
}

EncInst constrInstVfill(uint64_t precision, uint64_t imma, RegId Xd, uint64_t immb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::VFILL_32);
  embdInstVfill_32Precision(inst, precision);
  embdInstVfill_32Imma(inst, imma);
  embdInstVfill_32Xd(inst, Xd);
  embdInstVfill_32Immb(inst, immb);
  return inst;
}


}; // namespace basim
