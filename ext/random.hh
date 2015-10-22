//----------------------------------------------------------------------
//
// random.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Random number generation functions.  */

#ifndef __RANDOM_HH__
#define __RANDOM_HH__

//----------------------------------------------------------------------
// classes
//------------------------------------------------------------------------

/* Shuffled L'Ecuyer random number generator.

   Generator for uniform deviates based on 

     L'Ecuyer, P. 1988, Communications of the ACM, vol. 31, pp. 742-774

   as described and implemented as the 'ran2' function in

     Press, William H. et al., Numerical Recipes in C, Cambridge
     University Press, 1988, p. 282.

   This generator is based on two multiplicative congruential generators
   with factors 'a1' and 'a2' and moduli 'm1' and 'm2, with
   multiplication performed with Schrage's algorith.  The values from
   the two sequences are combined, and the sequence is shuffled using a
   table of 'tab_size'.  

   The period of the generator is about 2.3 x 10^18.

*/
class ShuffledLEcuyerRandom
{
public:

  /* Create a new generator.

     'seed' -- A positive integer seed value.  If zero, a seed is chosen
     using the system time. 
  */
  ShuffledLEcuyerRandom(long seed=0);
  
  /* Initialize the generator. 

     'seed' -- A positive integer seed value.  If zero, a seed is chosen
     using the system time. 
  */
  void initialize(long seed=0);

  /* Return a uniform deviate between 0 inclusive and 1 exclusive.  */
  float random();

private:

  // Forbid copies.
  ShuffledLEcuyerRandom(const ShuffledLEcuyerRandom&);

  // Shuffle table size.
  const static int table_size_ = 32;

  // State variables for the congruential generators.
  long state1_;
  long state2_;

  // State of the combined generator; used for shuffling.
  long last_;

  // The shuffle table.
  long shuffle_table_[table_size_];

};

//----------------------------------------------------------------------

#endif  // #ifndef __RANDOM_HH__
