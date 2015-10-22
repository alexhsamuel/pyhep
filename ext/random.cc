//----------------------------------------------------------------------
//
// random.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Random number generation functions.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <cstddef>
#include <sys/time.h>

#include "random.hh"

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

namespace {

// Constants for the first congruential generator.
const static long m1 = 2147483563;
const static long a1 = 40014;
const static long q1 = 53668;
const static long r1 = 12211;

// Constants for the second congruential generator.
const static long m2 = 2147483399;
const static long a2 = 40692;
const static long q2 = 52774;
const static long r2 = 3791;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

inline float
min(float v1,
    float v2)
{
  return (v1 < v2) ? v1 : v2;
}


}  // anonymous namespace

//----------------------------------------------------------------------
// methods
//----------------------------------------------------------------------

ShuffledLEcuyerRandom::ShuffledLEcuyerRandom(long seed)
{
  initialize(seed);
}


void
ShuffledLEcuyerRandom::initialize(long seed)
{
  // If no seed was specified, construct one from the system time.
  if (seed == 0) {
    struct timeval now;
    int result = gettimeofday(&now, NULL);
    assert(result == 0);
    seed = now.tv_sec ^ now.tv_usec;
  }

  // Initialize.
  assert(seed > 0);
  state1_ = seed;
  state2_ = seed;

  // Load the shuffle table (after eight warm-ups).
  for (long j = table_size_ + 7; j >= 0; j--) {
    long k = state1_ / q1;
    state1_ = a1 * (state1_ - k * q1) - k * r1;
    if (state1_ < 0)
      state1_ += m1;
    if (j < table_size_)
      shuffle_table_[j] = state1_;
  }
  last_ = shuffle_table_[0];
}


float
ShuffledLEcuyerRandom::random()
{
  long k;
  static float inv_m1 = 1.0 / m1;

  // Next value from the first congruential generator.
  k = state1_ / q1;
  state1_ = a1 * (state1_ - k * q1) - k * r1;
  if (state1_ < 0)
    state1_ += m1;

  // Next value from the second congruential generator.
  k = state2_ / q2;
  state2_ = a2 * (state2_ - k * q2) - k * r2;
  if (state2_ < 0)
    state2_ += m2;

  // Combine and shuffle.
  int j = last_ / (1 + (m1 - 1) / table_size_);
  last_ = shuffle_table_[j] - state2_;
  shuffle_table_[j] = state1_;
  if (last_ < 1)
    last_ += m1 - 1;

  // Make sure we never return 1.0.
  return min(last_ * inv_m1, 1.0 - 1.2e-7);
}


