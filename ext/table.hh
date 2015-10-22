//----------------------------------------------------------------------
//
// table.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Flat-file data table implementation and file format.  */

#ifndef __TABLE_HH__
#define __TABLE_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <fcntl.h>
#include <string>
#include <sys/types.h>
#include <unistd.h>
#include <vector>

#include "value.hh"

//----------------------------------------------------------------------
// forward declarations
//----------------------------------------------------------------------

namespace table {

class Row;

//----------------------------------------------------------------------
// exception classes
//----------------------------------------------------------------------

class NoColumn 
{
public:

  NoColumn(const std::string& column_name);
  const std::string column_name_;

};


inline
NoColumn::NoColumn(const std::string& column_name)
  : column_name_(column_name)
{
}


class NotWritable
{
};


class NoRow
{
public:

  NoRow(int row_number) : row_number_(row_number) {}
  const int row_number_;

};


class FileError
{
public:

  FileError(const std::string& message);
  const std::string message_;

};


inline
FileError::FileError(const std::string& message)
  : message_(message)
{
}


class WrongColumnType
{
};


//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

enum ColumnType
{
  TYPE_NONE = -1,
  TYPE_BOOL = 0,
  TYPE_INT_8,
  TYPE_INT_16,
  TYPE_INT_32,
  TYPE_FLOAT_32,
  TYPE_FLOAT_64,
  TYPE_COMPLEX_64,
  TYPE_COMPLEX_128,
  TYPE_LAST
};


//----------------------------------------------------------------------

#if 0
template<typename TYPE>
struct ColumnTypeTemplate
{
  static ColumnType type;
};


template<>
ColumnType
ColumnTypeTemplate<bool>::type = TYPE_BOOL;


template<>
ColumnType
ColumnTypeTemplate<char>::type = TYPE_INT_8;


template<>
ColumnType
ColumnTypeTemplate<short>::type = TYPE_INT_16;


template<>
ColumnType
ColumnTypeTemplate<long>::type = TYPE_INT_32;


template<>
ColumnType
ColumnTypeTemplate<float>::type = TYPE_FLOAT_32;


template<>
ColumnType
ColumnTypeTemplate<double>::type = TYPE_FLOAT_64;
#else

template<typename TYPE>
ColumnType
getColumnType();

template<>
inline ColumnType
getColumnType<bool>()
{
  return TYPE_BOOL;
}


template<>
inline ColumnType
getColumnType<char>()
{
  return TYPE_INT_8;
}


template<>
inline ColumnType
getColumnType<short>()
{
  return TYPE_INT_16;
}


template<>
inline ColumnType
getColumnType<long>()
{
  return TYPE_INT_32;
}


template<>
inline ColumnType
getColumnType<float>()
{
  return TYPE_FLOAT_32;
}


template<>
inline ColumnType
getColumnType<double>()
{
  return TYPE_FLOAT_64;
}
#endif


//----------------------------------------------------------------------

class Column
{
public:

  Column(const std::string& name, const ColumnType type);
  Column(const Column& column);

  const std::string& getName() const;
  ColumnType getType() const;

private:

  std::string name_;
  ColumnType type_;

};


//----------------------------------------------------------------------

class Schema
{
public:

  Schema();
  virtual ~Schema();

  int getNumColumns() const;
  int whichColumn(const std::string& name) const throw (NoColumn);
  const Column& getColumn(int column_index) const;
  size_t getColumnOffset(int column_index) const;

  size_t getSize() const;

protected:

  struct ColumnRecord 
  {
    Column column_;
    size_t offset_;
  };

  std::vector<ColumnRecord> columns_;
  size_t size_;

};


class CustomSchema
  : public Schema
{
public:

  CustomSchema(size_t size=0);
  virtual ~CustomSchema();

  void addColumn(const Column& column, size_t offset);

};


class AutoSchema
  : public Schema
{
public:

  AutoSchema();
  virtual ~AutoSchema();

  void addColumn(const Column& column);

};


// FIXME: This is disabled; is it worth fixing?
#if 0
template<class STRUCT>
class StructSchema
  : public Schema
{
public:

  StructSchema();
  virtual ~StructSchema();

  template<typename FIELD_TYPE>
  void addColumn(const std::string& name, FIELD_TYPE STRUCT::* offset);

  void fillRow(Row* row, const STRUCT* structure) const;

private:

  void addColumn(const std::string& name, int offset, ColumnType type);

  std::vector<int> offsets_;

};
#endif


class Row
{
public:

  Row(const Schema* schema);
  ~Row();

  const Schema* getSchema() const
    { return schema_; }

  char* getBuffer() const
    { return data_; }

  Value getValue(int column_index) const throw (WrongColumnType);
  void setValue(int column_index, const Value& value);

private:

  const Schema* const schema_;
  char* data_;

};


class Table
{
protected:

  Table(const Schema* schema, bool writable)
    : schema_(schema), writable_(writable) {}

public:

  virtual ~Table();

  const Schema* getSchema() const
    { return schema_; }
  const bool isWritable() const
    { return writable_; }
  
  virtual int64_t getNumRows() const = 0;
  virtual void read(int64_t row_number, Row* row) = 0;
  virtual int append(const Row* row) = 0;
  virtual std::string getMetadata() const = 0;
  virtual void setMetadata(const std::string& data) = 0;

protected:

  const Schema* schema_;
  bool writable_;

};


class FileTable
  : public Table
{
public:

  ~FileTable();

  virtual int64_t getNumRows() const;
  virtual void read(int64_t row_number, Row* row);
  virtual int append(const Row* row);
  virtual std::string getMetadata() const;
  virtual void setMetadata(const std::string& data);

  static FileTable* create(const Schema* schema,
			   const std::string& path, 
			   mode_t mode=0666);
  static FileTable* open(const std::string& path, 
			 const std::string& mode);
  std::string getPath() const
    { return path_; }

protected:

  FileTable(const std::string& path, int flags=O_RDONLY);

private:

  const std::string path_;
  int fd_;

  off64_t first_row_offset_;
  off64_t row_size_;

  int64_t num_rows_;

};


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern size_t
getTypeSize(ColumnType type);

extern const char*
getTypeName(ColumnType type);

extern ColumnType
getTypeByName(const char* name);

//----------------------------------------------------------------------
// inline methods
//----------------------------------------------------------------------

inline
Column::Column(const std::string& name,
	       const ColumnType type)
  : name_(name),
    type_(type)
{
}


inline
Column::Column(const Column& column)
  : name_(column.name_),
    type_(column.type_)
{
}


inline const std::string&
Column::getName()
  const
{
  return name_;
}


inline ColumnType
Column::getType()
  const
{
  return type_;
}


//----------------------------------------------------------------------

inline
Schema::Schema()
  : size_(0)
{
}


inline int
Schema::getNumColumns()
  const
{
  return columns_.size();
}


inline const Column&
Schema::getColumn(int column_index)
  const
{
  return columns_[column_index].column_;
}


inline size_t
Schema::getColumnOffset(int column_index)
  const
{
  return columns_[column_index].offset_;
}


inline size_t
Schema::getSize()
  const
{
  return size_;
}


//----------------------------------------------------------------------

inline
CustomSchema::CustomSchema(size_t size)
{
  size_ = size;
}


inline
CustomSchema::~CustomSchema()
{
}


inline void
CustomSchema::addColumn(const Column& column,
			size_t offset)
{
  ColumnRecord record = { column, offset };
  columns_.push_back(record);
}


//----------------------------------------------------------------------

#if 0
template<class STRUCT>
inline
StructSchema<STRUCT>::StructSchema()
{
}


template<class STRUCT>
inline
StructSchema<STRUCT>::~StructSchema()
{
}


template<class STRUCT>
template<typename FIELD_TYPE>
inline void
StructSchema<STRUCT>::addColumn(const std::string& name,
				FIELD_TYPE STRUCT::* offset)
{
  addColumn(name, (int) &(((STRUCT*) NULL)->*offset),
	    getColumnType<FIELD_TYPE>());
}


template<class STRUCT>
inline void
StructSchema<STRUCT>::fillRow(Row* row,
			      const STRUCT* structure)
  const
{
  int num_columns = columns_.size();
  for (int c = 0; c < num_columns; ++c) {
    const char* field_address = ((const char*) structure) + offsets_[c];
    row->setValue(c, (void*) field_address);
  }
}


template<class STRUCT>
inline void
StructSchema<STRUCT>::addColumn(const std::string& name,
				int offset,
				ColumnType type)
{
  Column column(name, type);
  ColumnRecord record = { column, size_ };
  columns_.push_back(record);
  size_ += getTypeSize(column.getType());
  offsets_.push_back(offset);
}
#endif


//----------------------------------------------------------------------

inline int64_t
FileTable::getNumRows()
  const
{
  return num_rows_;
}


//----------------------------------------------------------------------

}  // namespace table


#endif  // #ifndef __TABLE_HH__
