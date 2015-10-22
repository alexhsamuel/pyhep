#ifndef __INSTCOUNT_HH__
#define __INSTCOUNT_HH__

#include <cstdlib>
#include <iostream>
#include <set>

#include "python.hh"


template<class CLASS>
class InstanceCounter
{
public:

  InstanceCounter() {}
  ~InstanceCounter() { reportInstances(); }

  void add(CLASS* instance);
  void remove(CLASS* instance);

  void reportInstances(std::ostream& out=std::cout);

private:

  std::set<CLASS*> instances_;

};


template<class CLASS>
inline void
InstanceCounter<CLASS>::add(CLASS* instance)
{
  if (instances_.find(instance) != instances_.end()) {
    std::cerr << "ERROR: duplicate instance at " 
	      << (void*) instance << '\n';
    abort();
  }

  instances_.insert(instance);
}


template<class CLASS>
inline void
InstanceCounter<CLASS>::remove(CLASS* instance)
{
  typename std::set<CLASS*>::iterator position = instances_.find(instance);
  if (position == instances_.end()) {
    std::cerr << "ERROR: removal of nonexistent instance at "
	      << (void*) instance << '\n';
    abort();
  }

  instances_.erase(position);
}


template<class CLASS>
void
InstanceCounter<CLASS>::reportInstances(std::ostream& out)
{
  if (instances_.empty())
    return;

  if (true) 
    out << instances_.size() << " leaked instances of " 
	<< CLASS::type.tp_name;
  else {
    out << "instances of " << CLASS::type.tp_name << ": \n";
    for (typename std::set<CLASS*>::const_iterator iter = instances_.begin();
	 iter != instances_.end();
	 ++iter) 
      out << (void*) *iter << ' ' << (*iter)
	  << " (" << (*iter)->ob_refcnt << " refs)\n";
  }

  out << std::endl;
}


#endif  // #ifndef __INSTCOUNT_HH__
