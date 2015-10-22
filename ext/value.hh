//----------------------------------------------------------------------
//
// value.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* A variadic type.  */

#ifndef __VALUE_HH__
#define __VALUE_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <complex>
#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>

#ifdef __PYTHON_HH__
#define PYTHON 1
#else
#define PYTHON 0
#endif

//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

class Value
{
public:

  enum Type
  {
    TYPE_NONE,
    TYPE_LONG,
    TYPE_DOUBLE,
    TYPE_BOOL,
    TYPE_COMPLEX,
#if PYTHON
    TYPE_OBJECT,
#endif
  };

  static Value make(long value);
  static Value make(double value);
  static Value make(bool value);
  static Value make(std::complex<double> value);
  
  Value();
  Value(const Value&);
  ~Value();
  void operator = (const Value&);

  Type getType() const { return type_; }
  template <typename TYPE> TYPE as() const;

  long as_long() const;
  double as_double() const;
  bool as_bool() const;
  std::complex<double> as_complex() const;

  long cast_as_long() const;
  double cast_as_double() const;
  bool cast_as_bool() const;
  std::complex<double> cast_as_complex() const;

  std::string asString() const;
  void write(std::ostream& os) const;

#if PYTHON
  static Value make(Py::Object* object);
  Py::Object* as_object() const;
  Py::Object* cast_as_object() const;
#endif

private:

  Type type_;

  void checkType(Type type) const;

  union {
    long long_;
    double double_;
    bool bool_;
    double complex_[2];
#if PYTHON
    Py::Object* object_;
#endif
  };
};


//----------------------------------------------------------------------
// exceptions
//----------------------------------------------------------------------

class TypeError
{
public:

  TypeError(Value::Type requested_type, Value::Type actual_type);

  Value::Type requested_type_;
  Value::Type actual_type_;

};


inline
TypeError::TypeError(Value::Type requested_type,
		     Value::Type actual_type)
  : requested_type_(requested_type),
    actual_type_(actual_type)
{
}


//----------------------------------------------------------------------
// inline methods
//----------------------------------------------------------------------

inline
Value::Value()
  : type_(TYPE_NONE)
{
}


inline
Value::Value(const Value& value)
{
  memcpy(this, &value, sizeof(Value));
#if PYTHON
  if (type_ == TYPE_OBJECT)
    Py_INCREF(object_);
#endif
}


inline
Value::~Value()
{
#if PYTHON
  if (type_ == TYPE_OBJECT)
    Py_DECREF(object_);
#endif
}


inline void
Value::operator = (const Value& value)
{
  memcpy(this, &value, sizeof(Value));
#if PYTHON
  if (type_ == TYPE_OBJECT)
    Py_INCREF(object_);
#endif
}


inline Value
Value::make(long value)
{
  Value v;
  v.type_ = TYPE_LONG;
  v.long_ = value;
  return v;
}


inline Value
Value::make(double value)
{
  Value v;
  v.type_ = TYPE_DOUBLE;
  v.double_ = value;
  return v;
}


inline Value
Value::make(bool value)
{
  Value v;
  v.type_ = TYPE_BOOL;
  v.bool_ = value;
  return v;
}


inline Value
Value::make(std::complex<double> value)
{
  Value v;
  v.type_ = TYPE_COMPLEX;
  v.complex_[0] = std::real(value);
  v.complex_[1] = std::imag(value);
  return v;
}


#if PYTHON
inline Value
Value::make(Py::Object* object)
{
  Value v;
  v.type_ = TYPE_OBJECT;
  v.object_ = newRef(object);
  return v;
}
#endif


inline long
Value::as_long()
  const
{
  checkType(TYPE_LONG);
  return long_;
}


inline double
Value::as_double()
  const
{
  checkType(TYPE_DOUBLE);
  return double_;
}


inline bool
Value::as_bool()
  const
{
  checkType(TYPE_BOOL);
  return bool_;
}


inline std::complex<double>
Value::as_complex()
  const
{
  checkType(TYPE_COMPLEX);
  return std::complex<double>(complex_[0], complex_[1]);
}


#if PYTHON
inline Py::Object*
Value::as_object()
  const
{
  checkType(TYPE_OBJECT);
  RETURN_OBJ_REF(object_);
}
#endif


inline long
Value::cast_as_long()
  const
{
  switch (type_) {
  case TYPE_NONE:
    throw TypeError(TYPE_LONG, TYPE_NONE);
  case TYPE_LONG:
    return long_;
  case TYPE_DOUBLE:
    return (long) double_;
  case TYPE_BOOL:
    return (long) bool_;
  case TYPE_COMPLEX:
    throw TypeError(TYPE_LONG, TYPE_COMPLEX);
#if PYTHON
  case TYPE_OBJECT:
    return object_->IntAsLong();
#endif
  default:
    abort();
  }
}


inline double
Value::cast_as_double()
  const
{
  switch (type_) {
  case TYPE_NONE:
    throw TypeError(TYPE_DOUBLE, TYPE_NONE);
  case TYPE_LONG:
    return (double) long_;
  case TYPE_DOUBLE:
    return double_;
  case TYPE_BOOL:
    return (double) bool_;
  case TYPE_COMPLEX:
    throw TypeError(TYPE_DOUBLE, TYPE_COMPLEX);
#if PYTHON
  case TYPE_OBJECT:
    return object_->FloatAsDouble();
#endif
  default:
    abort();
  }
}


inline bool
Value::cast_as_bool()
  const
{
  switch (type_) {
  case TYPE_NONE:
    throw TypeError(TYPE_BOOL, TYPE_NONE);
  case TYPE_LONG:
    return (bool) long_;
  case TYPE_DOUBLE:
    return (bool) double_;
  case TYPE_BOOL:
    return bool_;
  case TYPE_COMPLEX:
    return complex_[0] != 0 || complex_[1] != 0;
#if PYTHON
  case TYPE_OBJECT:
    return object_->IsTrue();
#endif
  default:
    abort();
  }
}


inline std::complex<double>
Value::cast_as_complex()
  const
{
  switch (type_) {
  case TYPE_NONE:
    throw TypeError(TYPE_COMPLEX, TYPE_NONE);
  case TYPE_LONG:
    return std::complex<double>(long_, 0);
  case TYPE_DOUBLE:
    return std::complex<double>(double_, 0);
  case TYPE_BOOL:
    return std::complex<double>(bool_ ? 1 : 0, 0);
  case TYPE_COMPLEX:
    return std::complex<double>(complex_[0], complex_[1]);
#if PYTHON
  case TYPE_OBJECT:
    return object_->AsComplex();
#endif
  default:
    abort();
  }
}


#if PYTHON
inline Py::Object*
Value::cast_as_object()
  const
{
  switch (type_) {
  case TYPE_NONE:
    throw TypeError(TYPE_BOOL, TYPE_NONE);
  case TYPE_LONG:
    return Py::Int::FromLong(long_);
  case TYPE_DOUBLE:
    return Py::Float::FromDouble(double_);
  case TYPE_BOOL:
    return Py::newBool(bool_);
  case TYPE_COMPLEX:
    return Py::Complex::FromDoubles(complex_[0], complex_[1]);
  case TYPE_OBJECT:
    RETURN_OBJ_REF(object_);
  default:
    abort();
  }
}
#endif


inline std::ostream& 
operator << (std::ostream& os, 
	     Value value)
{
  value.write(os);
  return os;
}


inline std::string
Value::asString()
  const
{
  std::ostringstream ss;
  ss << *this;
  return ss.str();
}


inline void
Value::write(std::ostream& os)
  const
{
  switch (type_) {
  case TYPE_NONE:
    os << "(none)";
    break;

  case TYPE_LONG:
    os << long_;
    break;

  case TYPE_DOUBLE:
    {
      // Always show at least one decimal place, to avoid ambiguity.
      char buf[32];
      snprintf(buf, sizeof(buf), "%f", double_);
      if (strchr(buf, '.') == NULL)
	snprintf(buf, sizeof(buf), "%.1f", double_);
      os << buf;
    }
    break;

  case TYPE_BOOL:
    os << (bool_ ? "true" : "false");
    break;

  case TYPE_COMPLEX:
    os << "(" << complex_[0] << "," << complex_[1] << ")";
    break;

#if PYTHON
  case TYPE_OBJECT:
    os << object_->ReprAsString();
    break;
#endif

  default:
    abort();
  }
}


inline void
Value::checkType(Value::Type type)
  const
{
  if (type != type_)
    throw TypeError(type, type_);
}


//----------------------------------------------------------------------

#endif  // #ifndef __VALUE_HH__
