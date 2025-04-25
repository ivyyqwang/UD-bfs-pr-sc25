/**
**********************************************************************************************************************************************************************************************************************************
* @file:	EventQ.hh
* @author:	Andronicus
* @date:
* @brief:   Header File for the Event Q
*           This class defines a EventQ to be used for the UpDown Lane
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __EventQ__H__
#define __EventQ__H__
#include "lanetypes.hh"
#include "types.hh"
#include <cstdlib>
#include <iostream>
#include <vector>
#include <queue>

namespace basim {

template <typename T> class EventQ {
private:
  /* Event Queue data */
  std::queue<T> _data;

  /* Capacity */
  size_t _capacity;

  /* Class Name*/
  const char *_name;

public:
  /**
   * @brief Construct a new EventQ Object
   *
   * @param size Size of the Queue, 0 - infinite
   */
  EventQ(size_t size = 0) : _capacity(size), _name(__FUNCTION__) {}

  //~EventQ(){~_data;}

  /**
   * @brief Push event into EventQ
   *
   * @param word sized event_word
   */
  bool push(T event) {
    // capacity 0 indicates infinte queue
    if (_data.size() < _capacity || (_capacity == 0)) {
      _data.push(event);
      return true;
    }
    return false;
  }
  /**
   * @brief Remove event from EventQ
   *
   * @param 64bit event word - event
   */
  bool pop(void) {
    if (_data.size() > 0) {
      _data.pop();
      //_data.erase(_data.begin());
      return true;
    }
    return false;
  }

  /**
   * @brief Peek into EventQ.Top
   *
   * @param 64bit event word - event
   */

  T& peek(void) {
    if (_data.size() > 0)
      return _data.front();
    else
      exit(1);
  }

  /**
   * @brief Get current size of queue
   *
   */

  size_t getSize(void) { return _data.size(); }
  
  /**
   * @brief Get if the queue is empty
   *
   */

  bool isEmpty(void) { return _data.empty(); }
  /**
   * @brief Get queue Capacity
   *
   */

  size_t getCapacity(void) { return _capacity; }

  /**
   * @brief Get name of object type (for debug logging)
   *
   */

  const char *name(void) { return _name; }
};

typedef EventQ<eventword_t> *EventQPtr;

} // namespace basim
#endif //!__EventQ__H__
