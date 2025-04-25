/**
**********************************************************************************************************************************************************************************************************************************
* @file:	scratchpadbank.hh
* @author:	Andronicus
* @date:	
* @brief:   Class file for UpDown Scratch Pad Bank
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __SCRATCHPADBANK__H__
#define __SCRATCHPADBANK__H__
#include <iostream>
#include <cstdlib>
#include "types.hh"
#include "lanetypes.hh"
#include "util.hh"
#include <memory>
#include <vector>

namespace basim
{

class ScratchPadBank
{
    /** @brief ScratchPad Bank per Lane
     *         
     */
private:
    /* Size of Scratchpad in bytes */
    const unsigned numBytes;
    
    /* Base Address of the Bank */
    Addr bankBaseAddr;

    /* Local nwid */
    //networkid_t nwid;

    /* data is stored in bytes to ease streaming programs and sub-byte accesses */
    uint8_t* bankBytes;

public:
    /* default constructor */
    ScratchPadBank(): numBytes(0), bankBytes(nullptr), bankBaseAddr(0){};
    
    /* allocate space equal to number of Bytes in Bank */
    ScratchPadBank(size_t _numBytes, Addr base=0): numBytes(_numBytes), bankBytes(new uint8_t[numBytes]), bankBaseAddr(base){};

    /* Bank access functions */
    void setBankBase(Addr bankbase){bankBaseAddr = bankbase;}

    /* Read N Bytes into ptr based on endianness */
    void readBytes(uint32_t nbytes, Addr addr, uint8_t* data){
        assert((addr >= bankBaseAddr) && (addr <= (bankBaseAddr + numBytes)));
#ifdef LITTLEENDIAN
            for(auto i = 0; i < nbytes; i++){
                data[i] = bankBytes[addr + i];
                BASIM_INFOMSG("SPDBank Read Addr[%lu]:%u", addr+i, data[i]);
            }
#else
            for(auto i = 0; i < nbytes; i++){
                data[i] = bankBytes[addr + (nbytes - i - 1)];
            }
#endif
    }
    
    /* Write N Bytes in same order as received */
    void writeBytes(uint32_t nbytes, Addr addr, uint8_t* data){
        assert((addr >= bankBaseAddr) && (addr <= (bankBaseAddr + numBytes)));
#ifdef LITTLEENDIAN
            for(auto i = 0; i < nbytes; i++){
                BASIM_INFOMSG("SPDBank Write Addr[%lu]:%u", addr+i, data[i]);
                bankBytes[addr + i] = data[i];
            }
#else
            for(auto i = 0; i < nbytes; i++){
                bankBytes[addr + (nbytes - i - 1)] = data[i];
            }
#endif
    }
    
    void readAllBank(uint8_t* data){
        memcpy(data, bankBytes, numBytes);
    }
    
    void writeAllBank(const uint8_t* data){
        memcpy(bankBytes, data, numBytes);
    }
    
    /* Read word in the right endian order (little) */
    word_t readWord(Addr addr){
        uint8_t data[WORDSIZE];
        word_t worddata = 0;
        readBytes(WORDSIZE, addr, data);
        for(auto i = 0; i < WORDSIZE; i++)
            worddata = worddata | ((static_cast<uint64_t>(data[i]) << (8*(i))) & bytemask(i));
            BASIM_INFOMSG("SPD ReadWord SPDBANK[%lu]:%lu", addr, worddata);
        return worddata;
    }
    
    /* Write word */
    void writeWord(Addr addr, word_t worddata){
        BASIM_INFOMSG("SPD WriteWord SPDBANK[%lu]:%lu", addr, worddata);
        uint8_t data[WORDSIZE];
        for(auto i = 0; i < WORDSIZE; i++)
            data[i] = (worddata & bytemask(i)) >> (8*(i));
        writeBytes(WORDSIZE, addr, data);
    }

    ~ScratchPadBank(){
        delete[] bankBytes;
    }
    
};

typedef ScratchPadBank* ScratchPadBankPtr;

} // namespace basim

#endif  //!__SCRATCHPADBANK__H__

