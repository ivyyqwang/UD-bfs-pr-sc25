//
// Created by alefel on 12/07/23.
//

#ifndef UPDOWN_MMESSAGE_H
#define UPDOWN_MMESSAGE_H

#include <iostream>
#include <iomanip>
#include <assert.h>
#include <memory>
#include "lanetypes.hh"

namespace basim {

    enum class MType{
        M1Type = 0,
        M2Type = 1,
        M3Type = 2,
        M3Type_M = 3,
        M4Type = 4,
        M4Type_M = 5,
        Store_R = 6,
        Read_R = 7,
        Simluation_Sync = 8,
    };

    class MMessage {
    private:
        // used to trace the source of the message
        eventword_t srcEventWord;
        Addr srcAddr;

        // Destination event word/Destination event label
        // The destination event word contains information about the event to be triggered into execution at the destination.
        eventword_t eventWord;

        // Continuation word / continuation event label
        // The continuation word to be triggered following the destination event's execution.
        eventword_t continuationWord;
        
        // when message can be popped
        uint64_t _when;

        // PayLoad len
        uint64_t len;

        // Payload data 
        //std::shared_ptr<word_t []> payload;
        word_t* payload;

        // Type of Message
        MType mtype;

        // Mode of messages
        uint8_t mode;

        // Destination Address
        Addr dstAddr;

        uint64_t dest_node_id;

        uint8_t isGlobal; // 0:local address, 1: global address, -1: others

    public:
        MMessage() = delete;

        MMessage(MMessage const &) = delete;

        //MMessage &operator=(MMessage const &) = delete;

        MMessage(eventword_t xc, eventword_t xe, MType _mtype) {
            setXc(xc);
            setXe(xe);
            mtype = _mtype;
            payload = nullptr;
            len = 0;
            srcAddr = 0;
            dstAddr = 0;
            srcEventWord = -1;
            // eventWord = -1;
            dest_node_id = -1;
            isGlobal = 0; // Default is local memory
        }

        ~MMessage(){
            if(payload != nullptr)
                delete[] payload;
        }

        void setIsGlobal(uint8_t _isGlobal) { isGlobal = _isGlobal; }

        uint8_t getIsGlobal() { return isGlobal; }

        void setDestNodeID(uint64_t nodeid) { dest_node_id = nodeid; }

        uint64_t getDestNodeID() { return dest_node_id; }

        void setXe(eventword_t newXe) { eventWord = newXe; }
        
        void setXc(eventword_t newXc) { continuationWord = newXc; }

        eventword_t getXe() { return eventWord; };

        eventword_t getXc() { return continuationWord; };

        uint64_t when() { return _when;};
        
        void setWhen(uint64_t when) {_when = when;}

        MType getType(){return mtype;}

        void setType(MType _type) { mtype = _type; }

        void addpayload(word_t* data){
            for(int i = 0; i < len; i++)
                payload[i] = data[i];
        }
        
        word_t* getpayload(){return payload;}
        
        bool isStore(){return ((mode & 0x1) == 1);}
        
        void setMode(int _mode){mode = _mode;}

        uint8_t getMode() {return mode;}
        
        void setLen(uint64_t _len){
            len = _len;
            if (payload != nullptr)
                delete[] payload;
            if(_len > 0)
                payload = new word_t[len];
            else
                payload = nullptr;
        }
        
        uint64_t getLen(){return len;}

        uint64_t getMsgSize() {
            /* FIXME: should the message type also be part of the message? */
            return (len + 1 /* Dst Event Word / Dst Addr*/ + 1 /* Continuation Word*/) * sizeof(word_t);
        }
        
        Addr getdestaddr() { return dstAddr; }
        
        void setdestaddr(Addr _destaddr) {dstAddr = _destaddr; }

        Addr getSrcAddr() { return srcAddr; }

        void setSrcAddr(Addr _srcAddr) { srcAddr = _srcAddr; }

        eventword_t getSrcEventWord() { return srcEventWord; }

        void setSrcEventWord(eventword_t _srcEventWord) { srcEventWord = _srcEventWord; }
    };

typedef MMessage* MMessagePtr;


    // Need to rewrite this.
    //inline std::ostream &operator<<(std::ostream &str, M1Message &mMessage) {
    //    str << "m: 0x" << std::hex << mMessage.getM() << ", len: 0x" << mMessage.getLen() << ", xptr: 0x"
    //        << mMessage.getXptr() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe();
    //    str << "(0x0" << std::setw(8) << std::setfill('0')
    //        << (mMessage.getM() << 26 || mMessage.getLen() << 22 || mMessage.getXptr() << 17 ||
    //            mMessage.getXc() << 12 || mMessage.getXe());
    //    str << ") " << std::dec;
    //    return str;
    //}

    //inline std::ostream &operator<<(std::ostream &str, M2Message &mMessage) {
    //    str << "destaddr: 0x" << std::hex << mMessage.getdestaddr() << "m: 0x" << mMessage.getM() << ", len: 0x"
    //        << mMessage.getLen() << ", xptr: 0x"
    //        << mMessage.getXptr() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe();
    //    str << "(0x0" << std::setw(8) << std::setfill('0')
    //        << (mMessage.getdestaddr() << 27 || mMessage.getM() << 25 || mMessage.getLen() << 22 ||
    //            mMessage.getXptr() << 17 ||
    //            mMessage.getXc() << 12 || mMessage.getXe()
    //                    << 7);
    //    str << ") " << std::dec;
    //    return str;
    //}

    //inline std::ostream &operator<<(std::ostream &str, M3Message &mMessage) {
    //    str << "destaddr: 0x" << std::hex << mMessage.getdestaddr() << "m: 0x" << mMessage.getM() << ", x2: 0x"
    //        << mMessage.getX2() << ", x1: 0x"
    //        << mMessage.getX1() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe();
    //    str << "(0x0" << std::setw(8) << std::setfill('0')
    //        << (mMessage.getdestaddr() << 27 || mMessage.getM() << 26 || mMessage.getX2() << 22 ||
    //            mMessage.getX1() << 17 ||
    //            mMessage.getXc() << 12 || mMessage.getXe()
    //                    << 7);
    //    str << ") " << std::dec;
    //    return str;
    //}

    //inline std::ostream &operator<<(std::ostream &str, M4Message &mMessage) {
    //    str << std::hex << "destaddr: 0x" << mMessage.getdestaddr() << "m: 0x" << mMessage.getM() << ", numops: 0x"
    //        << mMessage.getNumops() << ", xop: 0x"
    //        << mMessage.getXop() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe();
    //    str << "(0x0" << std::setw(8) << std::setfill('0')
    //        << (mMessage.getdestaddr() << 27 || mMessage.getM() << 26 || mMessage.getNumops() << 22 ||
    //            mMessage.getXop() << 17 ||
    //            mMessage.getXc() << 12 || mMessage.getXe()
    //                    << 7);
    //    str << ") " << std::dec;
    //    return str;
    //}
}

#endif //UPDOWN_MMESSAGE_H
