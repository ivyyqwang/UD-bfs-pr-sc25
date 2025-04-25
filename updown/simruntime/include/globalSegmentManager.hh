#pragma once
#include <cstdint>
#include <math.h>
#include <vector>

#include "debug.h"
#include "updown_config.h"
#include "memorySegments.h"

namespace UpDown {
namespace GSM {

/** \brief Global Segment Manager
 *
 * Global segment manager that allows to create new segments into the system
 *
 */
class global_segment_manager_t {

  std::vector<global_segment_t> segments;

public:
  global_segment_manager_t() {}

  /** \brief Create a new global segment
   *
   * \param virtual_base The virtual base address of the segment
   * \param virtual_limit The virtual limit of the segment (exclusive)
   * \param swizzle_mask Swizzle mask describing the segment
   * \param pyhisical_base The physical base address of the segment
   * \param accesss_flags The access flags of the segment
   *
   * \return The segment id of the new segment
   */
  uint64_t createSegment(uint64_t virtual_base, uint64_t virtual_limit,
                         swizzle_mask_t swizzle_mask,
                         physical_addr_t pyhisical_base,
                         uint8_t accesss_flags) {
    segments.emplace_back(virtual_base, virtual_limit, swizzle_mask,
                          pyhisical_base, accesss_flags);
    return segments.size() - 1;
  }

  /** \brief Find segment that contains a given virtual address
   *
   * \param virtual_address The virtual address to check
   *
   * \return The segment that contains the virtual address
   */
  global_segment_t *findSegment(uint64_t virtual_address) {
    for (auto &segment : segments) {
      if (segment.contains(virtual_address)) {
        return &segment;
      }
    }
    return nullptr;
  }

  /** \brief Get the physical address from a virtual address
   *
   * Given the current segment configuration (swizzling mask physical base),
   * calculate the phyisical address that results from a virutal address
   *
   */
  physical_addr_t getPhysicalAddr(uint64_t virtual_address) {
    global_segment_t *segment = findSegment(virtual_address);
    UPDOWN_ERROR_IF(segment == nullptr,
                    "Virtual address 0x%lX does not belong to any segment",
                    virtual_address);
    return segment->getPhysicalAddr(virtual_address);
  }
};

} // namespace GSM
} // namespace UpDown