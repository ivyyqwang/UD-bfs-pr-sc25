/**
**********************************************************************************************************************************************************************************************************************************
* @file:	sendbuffer.hh
* @author:	Andronicus
* @date:	
* @brief:   Header File for the Sendbuffer
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __STREAMBUFFER__H__
#define __STREAMBUFFER__H__
#include <iostream>
#include <cassert>
#include <cmath>
#include "lanetypes.hh"
#include "types.hh"

namespace basim
{
    

/**
 * @brief  StreamBuffer Class for UpDown 
 * 
 * 
 */
class StreamBuffer
{
private:
    // Byte Array - that is automatically loaded from LM in UpDown
    uint8_t *streamBytes;

    // Capacity of Stream Buffer in Bytes
    int capacity;
    int capacitybits;

    // Pointers and capacity of the Stream Buffer 
    uint32_t rdPtr; // essentially a copy of SBP[9:0]
    uint32_t wrPtr;

    // Current 
    int size;

    uint8_t bytemask(int numbits){
        uint32_t num = (0x00000001 << numbits) - 1;
        return static_cast<uint8_t>(num);
    }

public:
    /**
     * @brief Construct a new Stream Buffer object - Default
     * 
     */
    StreamBuffer(): streamBytes(nullptr), capacity(0), capacitybits(0), wrPtr(0), rdPtr(0), size(0){};

    /**
     * @brief Construct a new Stream Buffer object
     * 
     * @param capacity 
     */
    StreamBuffer(int capacity): streamBytes(new uint8_t[capacity]), capacity(capacity), wrPtr(0), rdPtr(0), size(0){
        capacitybits = capacity * 8;
    };

    /**
     * @brief Stream Buffer Empty?
     * 
     * @return true 
     * @return false 
     */
    bool empty() const {return size == 0;}
    
    int getSize() const {return size;}
    
    int getCapacity() const {return capacity;}

    uint8_t getByte(uint32_t rdptr){
        // Perform checks before reading
        assert(size > 0);
        uint8_t retByte = streamBytes[rdptr];

        // Reduce size 
        size -= 8;

        return retByte;
    }

    /**
     * @brief Get the Var Symbol from Stream Buffer - return it as a uint64_t
     * 
     * @param rdptr 
     * @param size 
     * @return uint64_t 
     */
    uint64_t getVarSymbol(Addr ptr, int fetchbits){
        // rdptr is the SBP bit pointer
        // Check if size
        int locwrptr = (size) % capacitybits; 
        int locrdptr = ptr % capacitybits; 
        int numbits = abs(locrdptr - locwrptr);
        // assert(fetchbits < numbits && "Not enough bits in StreamBuffer Refill to be done\n");
        int bitoffset = locrdptr % (8);
        int bytenumber = locrdptr / 8;
        uint8_t retbyte = 0;
        if((bitoffset + fetchbits) > 8){
            // get across two bytes
            uint8_t lowerbits = (streamBytes[bytenumber] >> bitoffset) & bytemask(8-bitoffset);
            uint8_t upperbits = ((streamBytes[(bytenumber+1)%capacity]  & bytemask(fetchbits - (8-bitoffset))) << (8-bitoffset));
            //BASIM_INFOMSG("lowerbyte:%d, upperbyte:%d, lowermask:%x uppermask:%x, lowerbits:%d, upperbits:%d\n", streamBytes[bytenumber], streamBytes[bytenumber + 1], bytemask(8-bitoffset), bytemask(fetchbits- (8-bitoffset)), lowerbits, upperbits);
            retbyte = upperbits | lowerbits;
        }else{
            retbyte = (streamBytes[bytenumber] >> bitoffset) & bytemask(fetchbits);
        }
        //size -= fetchbits;
        BASIM_INFOMSG("Reading from Stream Buffer at ptr:%d, Data:%d, After Write Occup:%d", locrdptr, retbyte, size);
        return static_cast<uint64_t>(retbyte);
    }

    void setSBPInternal(Addr sbp){
        rdPtr = sbp & 0x1FF;
    }

    void writeIntoSB(Addr wrptr, uint8_t data){
        // wrptr is the byte address of the SBP (SBP >> 3)? 
        // Use byte address directly and fetch that many bytes
        // Convert this to byte address
        // assert(size <= capacitybits);
        uint32_t addr = wrptr % capacity;
        streamBytes[addr] = data;
        //for(auto i = 0; i < capacityof(word_t); i++){
        //    streamBytes[(addr + i)%capacity] = ((data >> (8*i)) & 0xFF);
        //    BASIM_INFOMSG("Writing into Stream Buffer at ptr:%d, Data:%ld, After Write Occup:%d", addr + i, ((data >> 8*i) &0xFF), size);
        //}
        //size += 8;
        //if(size > capacitybits) //(case where we've reloaded some bits)
        //    size - ((rdPtr & 0x7));
    }

    ~StreamBuffer(){
        delete[] streamBytes;
    }
};

typedef StreamBuffer* StreamBufferPtr;

}//basim
#endif  //!__STREAMBUFFER__H__

