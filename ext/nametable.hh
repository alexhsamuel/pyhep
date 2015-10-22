//----------------------------------------------------------------------
//
// nametable.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Tokenize strings as small integers.  

A nametable is an association between strings and small positive
integers.  Once a name is added to the table, it is immortal (for the
life of the nametable) and keeps the same integer index.  */

#ifndef NAMETABLE_HH
#define NAMETABLE_HH

#include <vector>

#include "python.hh"


class Nametable
{
public:

  Nametable();
  ~Nametable();

  /* Return the number of names in the table.  */
  int length() const;

  /* Look up or add 'name', and return its index.  */
  int find(const char* name);
  int find(Py::String* name);

  /* Return a new reference to the name corresponding to 'index'.  */
  Py::String* get(int index);
  
private:

  typedef std::vector<Py::String*> names_t;

  // The names in the table.
  names_t names_;

};


inline
Nametable::Nametable()
{
}


inline
Nametable::~Nametable()
{
  for (names_t::iterator iter = names_.begin(); 
       iter != names_.end();
       ++iter)
    (*iter)->DecRef();
}


inline int 
Nametable::length()
  const
{
  return names_.size();
}


inline int
Nametable::find(const char* name)
{
  Py::Ref<Py::String> name_str = Py::String::FromString(name);
  return find(name_str);
}


inline int
Nametable::find(Py::String* name_arg)
{
  Py::Ref<Py::String> name = Py::newRef(name_arg);
  Py::internInPlace(name);
  // Check if the name is already in the table.
  for (int i = 0; i < (int) names_.size(); ++i)
    if (names_[i] == name)
      // Yup, return its index.
      return i;
  // Not in the table.  Add it.
  names_.push_back(name.release());
  return names_.size() - 1;
}


inline Py::String* 
Nametable::get(int index)
{
  assert(index >= 0 && index < (int) names_.size());
  RETURN_NEW_REF(Py::String, names_[index]);
}


#endif  // #ifndef NAMETABLE_HH
