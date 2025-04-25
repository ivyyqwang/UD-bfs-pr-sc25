//
// Created by alefel on 19/07/23.
//

#ifndef UPDOWN_BUFFER_H
#define UPDOWN_BUFFER_H

#include <queue>
#include <vector>
#include <limits>
#include <cstdint>
#include <assert.h>
#include "debug.hh"
#include "mmessage.hh"
#include "tickobject.hh"


namespace  basim {
    template<typename T>
    class Buffer : public TickObject{
    public:
        //-- delete standard constructors
        //Buffer() = delete;
        //Buffer(Buffer const&) = delete;
        //Buffer& operator=(Buffer const&) = delete;

        /*!
         * \brief The Buffer system accepts elements from multiple sources and stores them in a queue.
         */
        Buffer(const uint32_t latency_) : latency(latency_), maxSize(std::numeric_limits<std::size_t>::max()) {
            idle = true;
            latencyCountdown = 0;
        }

        Buffer(const uint32_t latency_, const std::size_t maxSize_) : latency(latency_), maxSize(maxSize_) {
            idle = true;
            latencyCountdown = 0;
        }

        ~Buffer() {
            reset();
        }

        /*!
         * \brief Resets the buffer
         */
        void reset();

        /*!
         * \brief Peeks into the oldest element in the queue without removing it. Asserts that the packet is ready
         * to be popped.
         * \see hasData
         * \return the oldest element in the queue
         */
        T peek();

        /*!
         * \brief Removes the oldest element in the queue. Asserts that the packet is ready to be popped after
         * [latency] cycles.
         * \see hasData
         * \see latency
         */
        void pop();

        /*!
         * \brief Adds a new element to the beginning of the queue.
         * \param element: The element to be added.
         */
        void push(T element);

        /*!
         * \brief Adds a new element to the beginning of the queue.
         * \param element: The element to be added.
         * \param latency_: This element has a specific latency and should be injected into the output port only then
         */
        void push(T element, uint32_t latency_);

        /*!
         * \brief Execute 1 tick
         */
        void tick(uint64_t timestamp = 0) override;

        /*!
         * \brief Return the current occupancy level of the queue
         * \return The current number of elements in the queue
         */
        uint16_t size();

        /*!
         * \brief Returns a boolean indicating, if the buffer is ready
         * to receive more data.
         * \see hasData
         * \return true, if further elements can be stored, false otherwise.
         */
        bool isFull();

        /*!
         * \brief Returns a boolean indicating, if the buffer is empty
         * \see hasData
         * \return true, if the buffer is empty.
         */
        bool isEmpty();

        /*!
         * \brief There is a difference between !isFull and hasData. A packet
         * that is stored in the buffer is not available immediately as the clock
         * cycle needs to be updated first. This method considers this hardware
         * constraint. It is configurable in the constructor (the latency
         * parameter).
         * \see latency
         * \see pop
         * \see peek
         * @return True, if data is ready to be popped from the buffer or peeked into
         */
        bool hasData();


    private:
        std::queue<T> buffer;

        bool idle;
        const uint32_t latency;
        const uint64_t maxSize;

        /*
         * A quite rudimentary implementation of the latency hardware constraints of a buffer.
         * It only considers the very first packet after the buffer was empty. This first packet
         * becomes available only after [latency] cycles.
         */
        uint32_t latencyCountdown;

        void printBuffer();
    };


    template<typename T>
    void Buffer<T>::reset() {
        std::queue<T> empty;
        std::swap(buffer, empty);
        latencyCountdown = 0;
    }

    template<typename T>
    T Buffer<T>::peek() {
        assert(!isEmpty() && "The buffer is empty!");
        assert(latencyCountdown == 0 && "No element is ready yet!");
        return std::move(buffer.front());
    }

    template<typename T>
    void Buffer<T>::pop() {
        assert(!isEmpty() && "The buffer is empty!");
        assert(latencyCountdown == 0 && "No element is ready yet!");
        buffer.pop();
    }

    template<typename T>
    void Buffer<T>::push(T element) {
        buffer.push(std::move(element));
        //push(element, latency);
    }

    template<typename T>
    void Buffer<T>::push(T element, uint32_t latency_) {
        assert(!isFull() && "The buffer is full!");
        buffer.push(std::move(element));
        //printBuffer();

        if (idle) {
            idle = false;
            latencyCountdown = latency_;
        }
    }

    template<typename T>
    void Buffer<T>::tick(uint64_t timestamp) {
        //printBuffer();
        if (isEmpty()) {
            // no more elements
            idle = true;
        } else if (latencyCountdown > 0) {
            // a packet has been inserted in the buffer, but we are still waiting for it to become ready
            latencyCountdown--;
        }
    }

    template<typename T>
    uint16_t Buffer<T>::size() {
        return buffer.size();
    }

    template<typename T>
    bool Buffer<T>::isFull() {
        return buffer.size() >= maxSize;
    }

    template<typename T>
    bool Buffer<T>::isEmpty() {
        return buffer.empty();
    }

    template<typename T>
    bool Buffer<T>::hasData() {
        return !isEmpty() && latencyCountdown == 0;
    }

    template<typename T>
    void Buffer<T>::printBuffer() {
        for (T element: buffer) {
            BASIM_INFOMSG("element: ", element);
        }
    }
}

#endif //UPDOWN_BUFFER_H
