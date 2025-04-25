/**
**********************************************************************************************************************************************************************************************************************************
* @file:	util.cpp
* @author:	
* @date:	
*  @brief Implementation of functions in util.hh
**********************************************************************************************************************************************************************************************************************************
 */

#include "util.hh"
#include "types.hh"
#include "lanetypes.hh"
#include <ios>
#include <sstream>

namespace basim 
{

    word_t bytemask(uint8_t pos){
        return (static_cast<word_t>(0xFF) << ((pos << 3)));
    }

    // Assume bytes are in the right endian order
    word_t bytestoword(uint8_t* data){
        word_t worddata = 0;
        word_t tempdata;
#ifdef LITTLEENDIAN
        for(auto i = 0; i < WORDSIZE; i++){
            tempdata = static_cast<word_t>(data[i]);
            worddata = worddata | ((tempdata << (8*i)) & bytemask(i));
        }
#else
        for(auto i = WORDSIZE; i > 0; i--){
            tempdata = static_cast<word_t>(data[i]);
            worddata = worddata | ((tempdata[i] << (8*(WORDSIZE - i - 1))) & bytemask(WORDSIZE - i - 1));
        }
#endif
        return worddata;
    }
    
    word_t bytestowordoffset(uint8_t* data, int size, int offset){
        word_t subword = 0;
#ifdef LITTLEENDIAN
        for(auto i = 0; i < size; i++){
            subword = subword | ((data[i] << (8*(WORDSIZE-i-1))) & bytemask(WORDSIZE - i -1));
        }
#else
        for(auto i = size; i > 0; i--)
            subword = subword | ((data[i] << (8*(WORDSIZE - i - 1))) & bytemask(WORDSIZE - i - 1));
#endif
        subword = subword << (offset*8);
        return subword;
    }
    
    word_t swapbytes(int bytes, uint64_t src){
        word_t return_word = 0;
        for(auto i = 0; i < sizeof(word_t)/2; i++)
            return_word = return_word | (((src & bytemask(i)) >> 8*i) << (8*(WORDSIZE - i - 1)));
        return return_word;
    }

    Addr wordalignedaddr(Addr addr){
        return (((uint64_t)(-1) << 3) & addr);
    }
    
    word_t wordmask(Addr addr, int size){
        int offset = addr % WORDSIZE;
        uint64_t mask = 0;
        for(int i = offset; i < offset+size; i++)
            mask |= (static_cast<word_t>(0xFF) << ((i << 3)));
        return ~mask;
    }

    std::string addr2HexString(const void* ptr) {
        std::stringstream ss;
        ss << std::showbase << std::hex << ptr;
        return ss.str();
    }

} // namespace udbasim 
    