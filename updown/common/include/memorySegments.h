#pragma once
#include <cmath>
#include <cstdint>
#include <math.h>
#include <sys/types.h>

#include "debug.h"


class physical_addr_t {
  uint64_t nodeId;
  uint64_t nodePhysicalAddress;

public:
  /// \brief Construct a gsm::physical_addr_t with all fields set to 0
  physical_addr_t() : nodeId(0), nodePhysicalAddress(0) {}

  /** \brief Construct a gsm::physical_addr_t from a compressed word
   *
   * The structure of the word is as follows:
   * | 63 - 51 | 50 - 37 | 36 - 0 |
   * |  resrvd |  nodeId |  addr  |
   *
   */
  physical_addr_t(uint64_t compressed)
      : nodeId((compressed >> 37) & 0x3FFFULL),
        nodePhysicalAddress(compressed & 0x1FFFFFFFFFLL) {}

  /// \brief Construct a gsm::physical_addr_t from a nodeId and physical address
  physical_addr_t(uint64_t nodeId, uint64_t physicalAddress)
      : nodeId(nodeId), nodePhysicalAddress(physicalAddress) {}

  bool operator==(const physical_addr_t &other) const {
    return nodeId == other.nodeId && nodePhysicalAddress == other.nodePhysicalAddress;
  }

  bool operator!=(const physical_addr_t &other) const {
    return !(*this == other);
  }

  physical_addr_t operator+(const physical_addr_t &other) const {
    UPDOWN_ERROR_IF(
        other.nodeId + nodeId > 0x3FFFULL,
        "Node id overflow. The maximum number of nodes is 2^14 - 1");
    UPDOWN_ERROR_IF(other.nodePhysicalAddress + nodePhysicalAddress > 0xFFFFFFFFFULL,
                    "Physical address overflow. The maximum physical address "
                    "is 2^36 - 1");
    return physical_addr_t(nodeId + other.nodeId,
                           nodePhysicalAddress + other.nodePhysicalAddress);
  }

  physical_addr_t operator-(const physical_addr_t &other) const {
    UPDOWN_ERROR_IF(
        nodeId < other.nodeId,
        "Node id underflow. The minimum number of nodes is 0");
    UPDOWN_ERROR_IF(nodePhysicalAddress < other.nodePhysicalAddress,
                    "Physical address underflow. The minimum physical address "
                    "is 0");
    return physical_addr_t(nodeId - other.nodeId,
                           nodePhysicalAddress - other.nodePhysicalAddress);
  }

  /// \brief Returns the physical address of the node in a single word
  /// The structure of the word is as follows:
  /// | 63 - 51 | 50 - 37 | 36 - 0 |
  /// |  resrvd |  nodeId |  addr  |
  uint64_t getCompressed() { return (nodeId << 37) | nodePhysicalAddress; }

  /// \brief Returns the node id
  uint64_t getNodeId() { return nodeId; }

  /// \brief Returns the physical address of the node
  uint64_t getNodePhysicalAddress() { return nodePhysicalAddress; }
};

/** \brief Swizzle mask
 *
 *
 * The swizzle mask is a 64-bit word that determines how to swizzle the logical
 * address to obtain the physical address. The swizzle mask is a binary number
 * with 4 parts of interleaving consecutive 1s and 0s.
 *
 * The swizzle mask is encoded as follows:
 *
 * ```
 * 0bpppp_pppp_pppp_ffff_ffff_ffbb_bbbb_bbbb_bbbc_cccc_cccc_cccc_cccc_cccc_cccc
 * ```
 *
 * The number of elements in p, f, b, and c is not fixed. Instead, these
 * consecutive bits are counted to obtain each value
 *
 * The 4 parts are of the swizzle mask are:
 *
 * * c = Size of the block. It is used to determine how big a single block is in
 * by using 2^C where C is the number of consecutive bits in c
 * * b = Number of nodes. It is used to determine how many nodes are part of the
 * current segment using the equation 2^B where B is the number of consecutive
 * bits in b
 * * f = Filling bits. It is used to determine the size of p based on the
 * equation P = 64-(C+B+F). This is, these bits are not used.
 * * p = Number of physical address bits that are left untouched.
 *
 *
 * For example, if we have the value
 *
 * ```
 * 0b0000_0000_0000_0011_1111_1111_1111_1111_1111_1001_1111_1111_1111_1111_1111_1111
 *   |<-------------->|<------------------------->|<>|<--------------------------->|
 *      p = [63:51]          f = [50:28]       b = [27:26]      c = [25:0]
 * ```
 *
 * In this case, by counting the number of consecutive 1s and 0s we can obtain
 * P = size(p) = 13,
 * F = size(f) = 23,
 * B = size(b) = 2,
 * C = size(c) = 26
 *
 */
class swizzle_mask_t {
  uint64_t P;
  uint64_t F;
  uint64_t B;
  uint64_t C;
  uint64_t mask;

public:
  /** \brief Construct a swizzle mask based on the values F, B, and C
   *
   * A swizzle mas is a binary number of interleaving consecutive 1s and 0s.
   * See the documentation of the swizzle_mask field for more information.
   *
   * This function infers P from the values of F, B, and C with the following
   * formula:
   * P = 64 - F - B - C
   *
   * It also assumes, that C and F are composed of 1s, while B and P are
   * composed of 0s.
   *
   * \param F The number of consecutive 1s in the filling bits
   * \param B The number of consecutive 0s in the node bits
   * \param C The number of consecutive 1s in the block bits
   *
   * \return The swizzle mask
   */
  swizzle_mask_t(uint64_t P, uint64_t F, uint64_t B, uint64_t C)
      : P(P), F(F), B(B), C(C), mask(0) {
    UPDOWN_ERROR_IF(P + F + B + C != 64,
                    "The sum of P, F, B, and C must be 64 received %lu",
                    P + F + B + C);
    mask = 0;
    mask |= (1ULL << F) - 1;
    mask <<= B + C;
    mask |= (1ULL << C) - 1;
    UPDOWN_INFOMSG(
        "Creating swizzle mask with P=%lu, F=%lu, B=%lu, C=%lu, mask=0x%lX", P,
        F, B, C, mask);
  }

  /** \brief Get a swizzle mask from a 64-bit word
   *
   * Given a swizzle mask in the format described in the documentation of the
   * swizzle_mask field, this function will infer the values of P, F, B, and C
   *
   * \param mask The swizzle mask
   *
   */
  swizzle_mask_t(uint64_t mask) : mask(mask) {
    uint64_t tmp = mask;
    C = 0;
    while (tmp & 0x1) {
      C++;
      tmp >>= 1;
    }
    B = 0;
    while (!(tmp & 0x1)) {
      B++;
      tmp >>= 1;
    }
    F = 0;
    while (tmp & 0x1) {
      F++;
      tmp >>= 1;
    }
    P = 64 - C - B - F;
  }

  /** \brief copy constructor
   *
   * \param other The swizzle mask to copy
   */
  swizzle_mask_t(const swizzle_mask_t &other)
      : P(other.P), F(other.F), B(other.B), C(other.C), mask(other.mask) {}

  /// \brief Get the swizzle mask formatted
  uint64_t getMask() { return mask; }

  /// \brief Get the number of bits for padding (P) repspected in the swizzle
  uint64_t getP() { return P; }

  /// \brief Get the number of bits for filling (F)
  uint64_t getF() { return F; }

  /// \brief Get the number of bits that represent (B) used to obtain the number
  /// of nodes
  uint64_t getB() { return B; }

  /// \brief Get the number of bits that represent (C), the offset within the
  /// block
  uint64_t getC() { return C; }
};

/** \brief Global Segment Description
 *
 * This class describes a single global segment. A global segment is a
 * description that determines the distribution of data across multiple
 * nodes. The global segment manager will have multiple descriptions like this
 * one of different data distributions.
 *
 * A global segment has three address spaces representation. A virtual
 * representation that is exposed to the application process. A logical
 * representation that is also consecutive but it is divided into a set of
 * blocks. And a physical representation that is how the blocks are distributed
 * across the nodes.
 *
 * For example, an application may see memory from 0xFFFFF to 0x10FFF as a
 * plain virtual address space. The same data will have a logical representation
 * of 10 blocks of 4KB each starting at address 0xBB of the logical address
 * space. Block 1 will go from 0xBB to 0xBB + 4KB. Block 2 will go from 0xBB +
 * 4KB to 0xBB + 8KB. And so on. Finally, the physical representation will not
 * be contiguous, and its distribution is parametrized by a segment descriptor.
 * If we assume that data is distributed in 3 nodes, then the blocks will be
 * distributed across these three nodes in a round-robin fashion. Therefore,
 * Node 1 will have blocks 0, 3, 6 and 9; Node 2 will have blocks 1, 4, and 7;
 * and Node 3 will have blocks 2, 5, and 8.
 *
 * The global segment descriptor has the following fields
 *
 * 1. Virtual Base Address: Determines the location of the first byte in the
 * virtual address space of the process
 * 2. Virtual Limit: Determines the location of the last byte in the virtual
 * address
 * 3. Swizzle Mask: Determines how to swizzle the virtual address to obtain the
 * physical address. This will be explained below.
 * 4. Physical Base Address: Determines the location of the first byte in the
 * physical address space. This includes the node id and the node offset.
 * 5. Access Flags: Determines the access rights of the segment.
 *
 * ## Translating virtual to logical address
 *
 * The virtual address is translated to a logical address by subtracting the
 * virtual base address from the virtual address. The virtual limit is used for
 * bounds checking (security). The discussion below uses the logical address
 * space.
 *
 * ## Physical Base Address
 *
 * Global segments may start at any node, and at any offset within that node.
 * The physical base address (encoded in physical_base_t) is a 64-bit
 * word that contains the node id and node offset of the first byte of the
 * segment. The physical base address is used to determine the final physical
 * address from a given offset.
 *
 * ## Swizzle Address
 *
 * This assumes that we have a swizzle mask. See the documentation for
 * swizzle_mask_t to understand swizzle masks
 *
 * The Swizzled Address is obtained by splitting a logical address into 3
 * parts.
 *
 * | Padding | Block Number | Block Offset |
 * |--- P ---|----- B ------|----- C ------|
 *
 * The block offset is the offset within the block in the physical memory once
 * the block and node have been identified.
 *
 * Blocks are numbered in order, starting at 0 and increasing by 1 with each
 * block. Block numbers do not consider the node each block belongs to. This is,
 * the block number is the ID of the block in the logical address space.
 *
 * For example imagine we have 10 blocks distributed over 2 nodes. There will
 * be 5 blocks per node. However, each block will have a unique block number
 * starting from 0 to 9. The block number is used to determine the node and
 * block offset.
 *
 * To calculate the bits that form the block number we use P and C from the
 * swizzle mask
 *
 * BlockNumber = Addr[63-P:C]
 *
 * Once we have the block number, we can calculate the node offset and the block
 * number within that node.
 *
 * NodeOffset = BlockNumber % NumberOfNodes
 * BlockNumberInNode = BlockNumber / NumberOfNodes
 *
 * The final swizzled address is obtained by concatenating the following:
 *
 * 1. The padding bits of the original address (i.e., Addr[63:63-P] are left
 *    untouched.
 * 2. Add the node offset.
 * 3. Add the offset to the block number within the node.
 * 4. Add the block offset.
 *
 * The final swizzled address is given by:
 *
 * SwizzledAddress = paddingBits | nodeOffset | BlockNumberInBlock*SizeOfBlock +
 *                                              BlockOffset
 *
 * Where | is the concatenation operator for each bit field.
 *
 * The structure of the physical base address was as follows:
 * | 63 - 51 | 50 - 37 | 36 - 0 |
 * |  resrvd |  nodeId |  addr  |
 *
 * Therefore, we must shift the node number to the left by 37 bits.
 *
 * The swizzled address is then given by:
 *
 * SwizzledAddress = Addr[63:63-P] << (P-63) +
 *                   (NodeOffset << 37) +
 *                   (BlockNumberInNode*SizeBlock) +
 *                    BlockOffset
 *
 * Resolving this expression we obtain:
 *
 * SwizzledAddress = Addr[63:63-P] << (P-63) +
 *                   (BlockNumber % NumberOfNodes << 37) +
 *                   ((BlockNumber / NumberOfNodes)*SizeBlock) +
 *                    BlockOffset
 *
 * And Replacing these values based on the elements from the swizzle mask we
 * obtain:
 *
 * SwizzledAddress = Addr[63:63-P] << P + Addr[63-P:C] % 2^B << 37 +
 * (Addr[63-P:C] / 2^B << C) + Addr[C-1:0]
 *
 * Therefore, the final address is given by:
 *
 * SwizzledAddress[50:37] gives the node offset
 * SwizzledAddress[36:0] gives the physical address offset
 *
 * Once we have the SwizzledAddress, we can obtain the final address by
 * including the physical_base address. This is achieved by adding the base node
 * to the node offset, and the base address to the physical address offset.
 *
 * PhysicalAddress = PhysicalBase + SwizzledAddress
 *
 * Putting it all together, the algorithm to obtain the physical address from
 * the virtual address is as follows:
 *
 * 1. Validate the virtual address is within the virtual limit:
 * (virtual_base <= virtual_address < virtual_limit) && valid(access_flags)
 * 2. Calculate the logical address by add/sub the virtual base address
 * (logical_address = virtual_address - virtual_base)
 * 3. Using the swizzle mask, obtain the node offset and the block number within
 * the node
 * 4. Obtain the physical address by adding the physical base address to the
 * node offset and the block number within the node
 *
 * ## Access Flags
 * Two bits permission field
 * 00: non-defined/invalid
 * 01: read-only
 * 10: write-only
 * 11: read-write
 */
class global_segment_t {

public:
  /// \brief The virtual base address of the segment
  uint64_t virtual_base;
  /// \brief The virtual limit of the segment (exclusive)
  uint64_t virtual_limit;
  /// \brief Swizzle mask describing the segment
  swizzle_mask_t swizzle_mask;

  /// \brief The number of nodes in the segment
  uint64_t num_nodes;
  /// \brief The size of a single block in the segment
  uint64_t block_size;

  /** \brief The physical base address of the segment
   *
   * The physical base address is a 64-bit word that contains the node id and
   * node offset of the first byte of the segment.
   *
   * It uses the gsm::physical_addr_t class to store the node id and node
   * offset
   *
   * The physical based is used to obtaine the final nodeID and the final
   * physical address within such node.
   *
   */
  physical_addr_t physical_base;

  /// \brief The physical limit of the segment (exclusive)
  physical_addr_t physical_limit;

  /** \brief The access flags of the segment
   *
   * The access flag allows to specify if this is read, write, or both
   */
  uint8_t access_flags;

  global_segment_t(uint64_t virtual_base, uint64_t virtual_limit,
                   swizzle_mask_t swizzle_mask, physical_addr_t physical_base,
                   uint8_t access_flags)
      : virtual_base(virtual_base), virtual_limit(virtual_limit),
        swizzle_mask(swizzle_mask), num_nodes(1ULL << swizzle_mask.getB()),
        block_size(1ULL << swizzle_mask.getC()),
        physical_limit(physical_addr_t((virtual_limit - virtual_base)/num_nodes + physical_base.getCompressed())),
        physical_base(physical_base), access_flags(access_flags) {}

  global_segment_t(uint64_t virtual_base, uint64_t virtual_limit,
                   uint64_t plain_swizzle_mask, uint64_t compressed_physical_base,
                   uint8_t access_flags)
      : virtual_base(virtual_base), virtual_limit(virtual_limit),
        swizzle_mask(plain_swizzle_mask), num_nodes(1ULL << swizzle_mask.getB()),
        block_size(1ULL << swizzle_mask.getC()),
        physical_base(compressed_physical_base),
        physical_limit(physical_base.getNodeId() + num_nodes, 
          ceil((virtual_limit - virtual_base + 0.0)/(num_nodes*block_size))*block_size + physical_base.getNodePhysicalAddress()),
        access_flags(access_flags) {}

  global_segment_t() = delete;

  /** \brief Check if a given address belongs to this segment
   *
   * \param virtual_address The virtual address to check
   *
   * \return True if the address belongs to this segment, false otherwise
   *
   */
  bool contains(uint64_t virtual_address) {
    UPDOWN_INFOMSG("Checking if 0x%lX is in [0x%lX, 0x%lX)", virtual_address,
                   virtual_base, virtual_limit);
    return virtual_address >= virtual_base && virtual_address < virtual_limit;
  }

  bool containsPhysicalAddr(physical_addr_t physical_addr) {
    UPDOWN_INFOMSG("Checking if 0x%lX is in bounds nodes [%ld, %ld), address [0x%lX, 0x%lX)", 
                   physical_addr.getCompressed(), physical_base.getNodeId(), 
                   physical_limit.getNodeId(), physical_base.getNodePhysicalAddress(),
                  physical_limit.getNodePhysicalAddress());
    return physical_addr.getNodePhysicalAddress() >= physical_base.getNodePhysicalAddress() &&
           physical_addr.getNodePhysicalAddress() < physical_limit.getNodePhysicalAddress() &&
           physical_addr.getNodeId() >= physical_base.getNodeId() &&
           physical_addr.getNodeId() < physical_limit.getNodeId();
  }

  /** \brief Get the physical address from a virtual address
   *
   * Given the current segment configuration (swizzling mask physical base),
   * calculate the physical address that results from a virutal address
   *
   */
  physical_addr_t getPhysicalAddr(uint64_t virtual_address) {
    // 1. Check for bounds
    UPDOWN_ERROR_IF(!contains(virtual_address),
                    "Virtual address 0x%lX is out of "
                    "bounds [0x%lX, 0x%lX)",
                    virtual_address, virtual_base, virtual_limit);

    UPDOWN_INFOMSG("Getting physical address for virtual address 0x%lX",
                   virtual_address);
    // 2. Calculate the logical address
    uint64_t logical_address = virtual_address - virtual_base;
    UPDOWN_INFOMSG("Logical address 0x%lX", logical_address);

    // 3. Calculate the swizzled address
    uint64_t P = swizzle_mask.getP();
    uint64_t F = swizzle_mask.getF();
    uint64_t B = swizzle_mask.getB();
    uint64_t C = swizzle_mask.getC();
    UPDOWN_INFOMSG("Swizzle parameters P = %lu, F = %lu, B = %lu, C = %lu", P,
                   F, B, C);

    uint64_t blockNumber = (logical_address >> C) & ((1ULL << (B + F)) - 1);
    uint64_t nodeOffset = blockNumber % num_nodes;
    uint64_t blockNumberInNode = blockNumber / num_nodes;
    uint64_t blockOffset = logical_address & ((1ULL << C) - 1);
    UPDOWN_INFOMSG(
        "Block number 0x%lX, node offset 0x%lX, block number in node 0x%lX, "
        "block offset 0x%lX",
        blockNumber, nodeOffset, blockNumberInNode, blockOffset);
    uint64_t swizzledAddress = (logical_address & ~(~0ULL >> P)) |
                               nodeOffset << 37 |
                               blockNumberInNode * block_size + blockOffset;

    UPDOWN_INFOMSG("Swizzled address 0x%lX", swizzledAddress);
    // 4. Add the physical base address and return
    return physical_base + physical_addr_t(swizzledAddress);
  }

  uint64_t getVirtualAddr(uint64_t physical_addr) {
    return getVirtualAddr(physical_addr_t(physical_addr));
  }

  uint64_t getVirtualAddr(physical_addr_t physical_addr) {
    UPDOWN_INFOMSG("Getting virtual address for physical address 0x%lx",
                   physical_addr.getCompressed());
    // 1. Check for physical bounds
    // physical_addr_t physical_addr_t(physical_addr);
    UPDOWN_ERROR_IF(!containsPhysicalAddr(physical_addr),
                    "Physical address 0x%lX[%ld, 0x%lx] is out of "
                    "bounds nodes [%ld, %ld), address [0x%lX, 0x%lX)",
                    physical_addr.getCompressed(), physical_addr.getNodeId(), physical_addr.getNodePhysicalAddress(),
                    physical_base.getNodeId(), physical_limit.getNodeId(), physical_base.getNodePhysicalAddress(),
                    physical_limit.getNodePhysicalAddress());

    // 2. Calculate the physical offset 
    physical_addr_t physical_offset = physical_addr - physical_base;

    // 3. Calculate the logical address from physical offset
    uint64_t P = swizzle_mask.getP();
    uint64_t F = swizzle_mask.getF();
    uint64_t B = swizzle_mask.getB();
    uint64_t C = swizzle_mask.getC();
    UPDOWN_INFOMSG("Swizzle parameters P = %lu, F = %lu, B = %lu, C = %lu", P,
                   F, B, C);

    uint64_t logical_address = (physical_offset.getNodeId() >> B) << (B + F + C) |
                               (physical_offset.getNodePhysicalAddress() >> C) << (B + C) |
                               (physical_offset.getNodeId() & ((1ULL << B) - 1)) << (C) | 
                               (physical_offset.getNodePhysicalAddress() & (1ULL << C) - 1);
    UPDOWN_INFOMSG("Logical address 0x%lX", logical_address);

    // 4. Add the virtual base address and return
    uint64_t virtual_addr = virtual_base + logical_address;
    UPDOWN_INFOMSG("Virtual address 0x%lX", virtual_addr);

    // 5. Check for virtual bounds
    UPDOWN_ERROR_IF(!contains(virtual_addr),
                    "Virtual address 0x%lX(%lu) reverse-translated from 0x%lX[%ld, 0x%lx]  is out of "
                    "bounds [0x%lX, 0x%lX) ",
                    virtual_addr, virtual_addr, physical_addr.getCompressed(), physical_addr.getNodeId()
                    , physical_addr.getNodePhysicalAddress(), virtual_base, virtual_limit);

    return virtual_addr;
  }

  /** \brief Print the segment for debug.
   * 
   */
  void print_info() {
    printf("Global segment {virtual base = %ld(0x%lx), virtual limit = %ld(0x%lx), swizzle mask = %ld(0x%lx), number of nodes = %ld, size of block = %ld, physical base = %ld(0x%lx), physical limit = %ld(0x%lx), access permission = %d}\n", 
                virtual_base,  virtual_base, 
                virtual_limit, virtual_limit, swizzle_mask.getMask(), swizzle_mask.getMask(), num_nodes, block_size, physical_base.getNodePhysicalAddress(), physical_base.getNodePhysicalAddress(), physical_limit.getCompressed(), physical_limit.getCompressed(), access_flags);
  }

};

/**
 * @brief Class that defines local memory segments based on global segments
 * 
 */
class private_segment_t {
  /// \brief The virtual base address of the segment
  uint64_t virtual_base;
  /// \brief The virtual limit of the segment (exclusive)
  uint64_t virtual_limit;
  /// \brief Offset to get physical address from virtual address
  int64_t offset;
  /// \brief The physical base address of the segment
  uint64_t physical_base;
  uint64_t physical_limit;

  /** \brief The access flags of the segment
   *
   * The access flag allows to specify if this is read, write, or both
   */
  uint8_t access_flags;

public:
  private_segment_t(uint64_t virtual_base, uint64_t virtual_limit, int64_t offset,
                   uint8_t access_flags)
      : virtual_base(virtual_base), virtual_limit(virtual_limit),
        offset(offset),
        physical_base(virtual_base + offset),
        physical_limit(virtual_limit + offset),
        access_flags(access_flags) {}

  
  private_segment_t(uint64_t virtual_base, uint64_t virtual_limit, uint64_t phyisical_base,
                   uint8_t access_flags)
      : virtual_base(virtual_base), virtual_limit(virtual_limit),
        offset((int64_t) phyisical_base - virtual_base),
        physical_base(phyisical_base),
        physical_limit(virtual_limit + offset),
        access_flags(access_flags) {}

  private_segment_t() = delete;

  /** \brief Check if a given address belongs to this segment
   *
   * \param virtual_address The virtual address to check
   *
   * \return True if the address belongs to this segment, false otherwise
   *
   */
  bool contains(uint64_t virtual_address) {
    UPDOWN_INFOMSG("Checking if 0x%lX is in [0x%lX, 0x%lX)", virtual_address,
                   virtual_base, virtual_limit);
    return virtual_address >= virtual_base && virtual_address < virtual_limit;
  }

  bool containsPhysicalAddr(uint64_t physical_addr) {
    UPDOWN_INFOMSG("Checking if 0x%lX is in [0x%lX, 0x%lX)", physical_addr,
                   physical_base, physical_base);
    return physical_addr >= physical_base && physical_addr < physical_limit;
  }

  uint64_t getVirtualAddr(uint64_t physical_addr) {
    UPDOWN_INFOMSG("Getting virtual address for physical address 0x%lX",
                   physical_addr);
    // 1. Check for bounds
    // physical_addr_t physical_addr_t(physical_addr);
    UPDOWN_ERROR_IF(!containsPhysicalAddr(physical_addr),
                    "Physical address 0x%lX is out of "
                    "bounds [0x%lX, 0x%lX)",
                    physical_addr, physical_base, physical_limit);

    // 2. Subtract the offset and return
    return physical_addr - offset;
  }

  /** \brief Get the physical address from a virtual address
   *
   * Given the current segment configuration (swizzling mask physical base),
   * calculate the phyisical address that results from a virutal address
   *
   */
  uint64_t inline getPhysicalAddr(uint64_t virtual_address) {
    uint64_t physical_address = virtual_address + offset;
    UPDOWN_INFOMSG("Getting physical address for virtual address 0x%lX = 0x%lX",
                   virtual_address, physical_address);
    return physical_address;
  }

  /** \brief Print the segment for debug.
   * 
   */
  void inline print_info() {
    UPDOWN_INFOMSG("Private local segment {virtual base = %ld(0x%lx), virtual limit = %ld(0x%lx), offset = %ld(0x%lx), access permission = %d}", 
                virtual_base,  virtual_base, 
                virtual_limit, virtual_limit, offset, offset, access_flags);
  }
};
