/** @file util.h
 *  @brief Simple Utility functions to help with UpDown implementation
 *
 *  @author Andronicus
 *  @bug No known bugs.
 */

#ifndef UTIL_HH
#define UTIL_HH
#include "types.hh"

namespace basim {

word_t bytemask(uint8_t pos);

word_t bytestoword(uint8_t *data);

word_t swapbytes(int bytes, uint64_t src);

Addr wordalignedaddr(Addr addr);

word_t wordmask(Addr addr, int size);

std::string addr2HexString(const void* ptr);

} // namespace basim

#endif