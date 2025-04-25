//
// Created by alefel on 12/07/23.
//

#ifndef UPDOWN_MMESSAGE_H
#define UPDOWN_MMESSAGE_H

#include <iostream>
#include <iomanip>
#include <assert.h>
#include <memory>

namespace basim {

    class MMessage {
    private:

        unsigned opcode;

        /// Destination event word/Destination event label
        /// The destination event word contains information about the event to be triggered into execution at the destination.
        unsigned xe;

        /// Continuation word / continuation event label
        /// The continuation word to be triggered following the destination event's execution.
        unsigned xc;

    protected:
        void setXc(unsigned newXc) { xc = newXc & 0x1f; }

    public:
        MMessage() = delete;

        MMessage(MMessage const &) = delete;

        MMessage &operator=(MMessage const &) = delete;

        MMessage(unsigned xc, unsigned xe, unsigned opcode) {
            setXc(xc);
            setXe(xe);
            setOpcode(opcode);
        }

        void setOpcode(unsigned newOpcode) { opcode = newOpcode & 0x3f; }

        unsigned getOpcode() { return opcode; }

        void setXe(unsigned newXe) { xe = newXe & 0x1f; }

        unsigned getXe() { return xe; };

        unsigned getXc() { return xc; };
    };


class M1Message : public MMessage, public std::enable_shared_from_this<M1Message> {
    private:
        /// Data Pointer
        /// Pointer to the Local Memory to be attached to the message
        unsigned xptr;

        /// Length of data in words
        /// Number of words to be packed into send message starting at [xptr].
        unsigned len;

    protected:
        /// The access mode
        /// 1 - store, 0 - load
        unsigned m;

    public:
        M1Message() = delete;

        M1Message(M1Message const &) = delete;

        M1Message &operator=(M1Message const &) = delete;

        M1Message(bool store, unsigned len, unsigned xptr, unsigned xc, unsigned xe, unsigned opcode) : MMessage(xc, xe,
                                                                                                                 opcode) {
            setXptr(xptr);
            setLen(len);
            if (store) {
                setStore();
            } else {
                setLoad();
            }
        }

        void setXptr(unsigned newXptr) { xptr = newXptr & 0x1f; }

        unsigned getXptr() { return xptr; }

        void setLen(unsigned newLen) { xptr = newLen & 0x7; }

        unsigned getLen() { return len; }

        void setStore() { m |= 1; }

        void setLoad() { m &= 0xfffffffe; }

        unsigned getM() { return m; }
    };

    class M2Message : public M1Message, public std::enable_shared_from_this<M2Message> {
    private:
        unsigned xd;

    public:
        M2Message() = delete;

        M2Message(M2Message const &) = delete;

        M2Message &operator=(M2Message const &) = delete;

        M2Message(unsigned xd, bool store, bool continuationWordInReg, unsigned len, unsigned xptr, unsigned xc,
                  unsigned xe, unsigned opcode) : M1Message(store, len, xptr, xc, xe, opcode) {
            setXc(xc, continuationWordInReg);
            setXd(xd);
        }

        void setXd(unsigned newXd) { xd = newXd & 0x1f; }

        unsigned getXd() { return xd; }

        void setXc(unsigned newXc, bool continuationWordInReg) {
            if (continuationWordInReg) {
                assert(newXc < 32); // 32 registers
                m &= 0xfffffffd;
            } else {
                m |= 2;
            }
            MMessage::setXc(newXc);
        }
    };

    class M3Message : public MMessage, public std::enable_shared_from_this<M3Message> {
    private:
        /// Mode configuration
        unsigned m;

        /// Global Memory Address specifying the global memory address to load data from or store data to.
        unsigned xd;
        unsigned x1;
        unsigned x2;

    public:

        M3Message() = delete;

        M3Message(M3Message const &) = delete;

        M3Message &operator=(M3Message const &) = delete;

        M3Message(unsigned xd, bool store, unsigned x2, unsigned x1, unsigned xc,
                  unsigned xe, unsigned opcode) : MMessage(xc, xe, opcode) {
            setXd(xd);
            setX1(x1);
            setX2(x2);
            if (store) {
                setStore();
            } else {
                setLoad();
            }
        }

        void setX1(unsigned newX1) { x1 = newX1 & 0x1f; }

        unsigned getX1() { return x1; }

        void setX2(unsigned newX2) { x2 = newX2 & 0xf; }

        unsigned getX2() { return x2; }

        void setStore() { m |= 1; }

        void setLoad() { m &= 0xfffffffe; }

        unsigned getM() { return m; }

        void setXd(unsigned newXd) { xd = newXd & 0x1f; }

        unsigned getXd() { return xd; }
    };

    class M4Message : public MMessage, public std::enable_shared_from_this<M4Message> {
    private:
        /// Mode configuration
        unsigned m;
        unsigned xd;

        /// Start operand register
        unsigned xop;

        /// Number of operands
        unsigned numOps;

    public:
        M4Message() = delete;

        M4Message(M4Message const &) = delete;

        M4Message &operator=(M4Message const &) = delete;

        M4Message(unsigned xd, bool store, unsigned xop, unsigned numOps, unsigned xc,
                  unsigned xe, unsigned opcode) : MMessage(xc, xe, opcode) {
            setXd(xd);
            setNumops(numOps);
            setXop(xop);
            if (store) {
                setStore();
            } else {
                setLoad();
            }
        }

        void setXop(unsigned newXop) { xop = newXop & 0x1f; }

        unsigned getXop() { return xop; }

        void setNumops(unsigned newNumops) { numOps = newNumops & 0x7; }

        unsigned getNumops() { return numOps; }

        void setStore() { m |= 1; }

        void setLoad() { m &= 0xfffffffe; }

        unsigned getM() { return m; }

        void setXd(unsigned newXd) { xd = newXd & 0x1f; }

        unsigned getXd() { return xd; }
    };

    inline std::ostream &operator<<(std::ostream &str, M1Message &mMessage) {
        str << "m: 0x" << std::hex << mMessage.getM() << ", len: 0x" << mMessage.getLen() << ", xptr: 0x"
            << mMessage.getXptr() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe()
            << ", Opcode: 0x" << mMessage.getOpcode();
        str << "(0x0" << std::setw(8) << std::setfill('0')
            << (mMessage.getM() << 26 || mMessage.getLen() << 22 || mMessage.getXptr() << 17 ||
                mMessage.getXc() << 12 || mMessage.getXe()
                        << 7 || mMessage.getOpcode());
        str << ") " << std::dec;
        return str;
    }

    inline std::ostream &operator<<(std::ostream &str, M2Message &mMessage) {
        str << "xd: 0x" << std::hex << mMessage.getXd() << "m: 0x" << mMessage.getM() << ", len: 0x"
            << mMessage.getLen() << ", xptr: 0x"
            << mMessage.getXptr() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe()
            << ", Opcode: 0x" << mMessage.getOpcode();
        str << "(0x0" << std::setw(8) << std::setfill('0')
            << (mMessage.getXd() << 27 || mMessage.getM() << 25 || mMessage.getLen() << 22 ||
                mMessage.getXptr() << 17 ||
                mMessage.getXc() << 12 || mMessage.getXe()
                        << 7 || mMessage.getOpcode());
        str << ") " << std::dec;
        return str;
    }

    inline std::ostream &operator<<(std::ostream &str, M3Message &mMessage) {
        str << "xd: 0x" << std::hex << mMessage.getXd() << "m: 0x" << mMessage.getM() << ", x2: 0x"
            << mMessage.getX2() << ", x1: 0x"
            << mMessage.getX1() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe()
            << ", Opcode: 0x" << mMessage.getOpcode();
        str << "(0x0" << std::setw(8) << std::setfill('0')
            << (mMessage.getXd() << 27 || mMessage.getM() << 26 || mMessage.getX2() << 22 ||
                mMessage.getX1() << 17 ||
                mMessage.getXc() << 12 || mMessage.getXe()
                        << 7 || mMessage.getOpcode());
        str << ") " << std::dec;
        return str;
    }

    inline std::ostream &operator<<(std::ostream &str, M4Message &mMessage) {
        str << std::hex << "xd: 0x" << mMessage.getXd() << "m: 0x" << mMessage.getM() << ", numops: 0x"
            << mMessage.getNumops() << ", xop: 0x"
            << mMessage.getXop() << "Xc: 0x" << mMessage.getXc() << ", Xe: 0x" << mMessage.getXe()
            << ", Opcode: 0x" << mMessage.getOpcode();
        str << "(0x0" << std::setw(8) << std::setfill('0')
            << (mMessage.getXd() << 27 || mMessage.getM() << 26 || mMessage.getNumops() << 22 ||
                mMessage.getXop() << 17 ||
                mMessage.getXc() << 12 || mMessage.getXe()
                        << 7 || mMessage.getOpcode());
        str << ") " << std::dec;
        return str;
    }
}

#endif //UPDOWN_MMESSAGE_H
