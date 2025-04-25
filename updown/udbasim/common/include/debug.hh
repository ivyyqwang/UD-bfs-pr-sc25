/*
 * Copyright (c) 2021 University of Chicago and Argonne National Laboratory
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Author - Jose M Monsalve Diaz, 
 *
 * Helper functions to add debug comments, error messages and others
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>


#ifndef __BADEBUG__H__
#define __BADEBUG__H__

namespace basim
{

enum logLevel {
  ASSERT,
  WARNING,
  INFO,
  DETAILED,
};
  
#define __FILENAME__                                                          \
  (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)

// Macro for output of information, warning and error messages
#ifdef DEBUG_MODE

#define MAX_DEBUG_LEVEL 100

#ifndef DEBUG_MODE_LEVEL
#define DEBUG_MODE_LEVEL MAX_DEBUG_LEVEL
#endif


#define BASIM_ASSERT(assertion, message, ...)                                 \
  {                                                                           \
    for (; !(assertion); printf("[BASIM_ASSERT_FAIL: %s:%i] " message "\n",   \
                                __FILENAME__, __LINE__, ##__VA_ARGS__),       \
                         fflush(stderr), fflush(stdout), assert(0)) {         \
    }                                                                         \
  }

#define BASIM_WARNING(message, ...)                                           \
  {                                                                           \
    printf("[BASIM_WARNING: %s:%i] " message "\n", __FILENAME__, __LINE__,    \
           ##__VA_ARGS__);                                                    \
    fflush(stderr);                                                           \
    fflush(stdout);                                                           \
  }
#define BASIM_WARNING_IF(condition, message, ...)                             \
  {                                                                           \
    if (condition) {                                                          \
      printf("[BASIM_WARNING: %s:%i] " message "\n", __FILENAME__, __LINE__,  \
             ##__VA_ARGS__);                                                  \
      fflush(stderr);                                                         \
      fflush(stdout);                                                         \
    }                                                                         \
  }

#define BASIM_EMPTY                                                           \
  {                                                                           \
    printf("\n");                                                             \
    fflush(stderr);                                                           \
    fflush(stdout);                                                           \
  }

#define BASIM_ERROR_IF(condition, message, ...)                               \
  {                                                                           \
    if (condition) {                                                          \
      fprintf(stderr, "[BASIM_ERROR: %s:%i] " message "\n", __FILENAME__,     \
              __LINE__, ##__VA_ARGS__);                                       \
      fflush(stderr);                                                         \
      fflush(stdout);                                                         \
      assert(0 && message);                                                   \
    }                                                                         \
  }

#define BASIM_INFOMSG_LEVEL(level, message, ...)                              \
  if constexpr (level <= DEBUG_MODE_LEVEL) {                                  \
    printf("[BASIM_INFO: %s:%i] " message "\n", __FILENAME__, __LINE__,       \
           ##__VA_ARGS__);                                                    \
    fflush(stderr);                                                           \
    fflush(stdout);                                                           \
  }

#define BASIM_INFOMSG(message, ...)                                           \
 BASIM_INFOMSG_LEVEL(MAX_DEBUG_LEVEL, message, ##__VA_ARGS__)                 \

#define BASIM_INFOMSG_IF(condition, message, ...)                             \
  {                                                                           \
    if (condition) {                                                          \
      printf("[BASIM_INFO: %s:%i] " message "\n", __FILENAME__, __LINE__,     \
             ##__VA_ARGS__);                                                  \
      fflush(stderr);                                                         \
      fflush(stdout);                                                         \
    }                                                                         \
  }
#else
#define BASIM_ASSERT(assertion, message, ...) {}
#define BASIM_WARNING(message, ...) {}
#define BASIM_WARNING_IF(message, ...) {}
#define BASIM_EMPTY {}
#define BASIM_INFOMSG(message, ...) {}
#define BASIM_INFOMSG_IF(message, ...) {}
#define BASIM_EMPTY {}
#endif // END IF VERBOSE_MODE

#define BASIM_PRINT(message, ...)                                             \
  {                                                                           \
    printf("[BASIM_PRINT] ");                                                 \
    printf(message, ##__VA_ARGS__);                                           \
    printf("\n");                                                             \
    fflush(stderr);                                                           \
    fflush(stdout);                                                           \
  } 

#define BASIM_ERROR(message, ...)                                             \
  {                                                                           \
    fprintf(stderr, "[BASIM_ERROR: %s:%i] " message "\n", __FILENAME__,       \
            __LINE__, ##__VA_ARGS__);                                         \
    fflush(stderr);                                                           \
    fflush(stdout);                                                           \
    exit(2 && message);                                                       \
  }

#define BASIM_ERROR_IF(condition, message, ...)                               \
  {                                                                           \
    if (condition) {                                                          \
      fprintf(stderr, "[BASIM_ERROR: %s:%i] " message "\n", __FILENAME__,     \
              __LINE__, ##__VA_ARGS__);                                       \
      fflush(stderr);                                                         \
      fflush(stdout);                                                         \
      assert(0 && message);                                                   \
    }                                                                         \
  }

}//basim

#endif
