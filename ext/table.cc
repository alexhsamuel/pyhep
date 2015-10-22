//----------------------------------------------------------------------
//
// table.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <cerrno>
#include <complex>
#include <fcntl.h>
#include <libgen.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "table.hh"
#include "value.hh"

namespace table {

namespace {

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

const size_t
type_sizes[] = { 
  1,    // TYPE_BOOL
  1,    // TYPE_INT_8
  2,    // TYPE_INT_16
  4,    // TYPE_INT_32
  4,    // TYPE_FLOAT_32
  8,    // TYPE_FLOAT_64
  8,    // TYPE_COMPLEX_64
  16,   // TYPE_COMPLEX_128
 };


const char* const
type_names[] = {
  "bool",       // TYPE_BOOL
  "int8",       // TYPE_INT_8
  "int16",      // TYPE_INT_16
  "int32",      // TYPE_INT_32
  "float32",    // TYPE_FLOAT_32
  "float64",    // TYPE_FLOAT_64
  "complex64",  // TYPE_COMPLEX_64
  "complex128", // TYPE_COMPLEX_128
};


const int
file_format_magic_number = 0x11a66826;

const int
file_format_version_number = 6;


//----------------------------------------------------------------------
// private types
//----------------------------------------------------------------------

// We have stdint.h to provide int32_t etc. but nothing for similar
// floating-point types.  Define the ones we need here.

// FIXME: These need to be configured specifically for each
// architecture. 

typedef float
float32_t;

typedef double
float64_t;

typedef std::complex<float>
complex64_t;

typedef std::complex<double>
complex128_t;

//----------------------------------------------------------------------

struct FileFormatHeader
{
  /* A magic number, identifying this file as a table file.  */
  int magic_number_;

  /* The file format version number.  */
  int version_number_;

  /* The number of rows in the table.  */
  int num_rows_;

  /* The offset to the data for the first row.  */
  off64_t first_row_offset_;

  /* Ignored, but retained for file format compatibility.  */
  off64_t metadata_offset_;

  /* Ignored, but retained for file format compatibility.  */
  off64_t metadata_len_;
};


//----------------------------------------------------------------------

class Buffer 
{
public:

  Buffer(size_t size) : pointer_(new char[size]) {}
  ~Buffer() { delete[] pointer_; }

  char* const pointer_;

};


//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

inline size_t
xwrite(int fd,
       const void* buffer,
       size_t count)
  throw (FileError)
{
  size_t result = ::write(fd, buffer, count);
  if (result != count)
    throw FileError(strerror(errno));
  return count;
}


inline void
xread(int fd, 
      void* buffer,
      size_t count)
  throw (FileError)
{
  size_t result = ::read(fd, buffer, count);
  if (result != count)
    throw FileError(strerror(errno));
}


inline void
xseek(int fd,
      off64_t offset)
  throw (FileError)
{
  off64_t result = ::lseek64(fd, offset, SEEK_SET);
  if (result != offset)
    throw FileError(strerror(errno));
}


inline std::string
getMetadataPath(const std::string& path)
{
  return path + ".metadata";
}


size_t
writeSchema(int fd, 
	    const Schema* schema)
{
  assert(fd >= 0);
  assert(schema != NULL);
  size_t written = 0;

  size_t size = schema->getSize();
  written += xwrite(fd, &size, sizeof(size_t));

  int num_columns = schema->getNumColumns();
  written += xwrite(fd, &num_columns, sizeof(int));

  for (int c = 0; c < num_columns; ++c) {
    const Column& column = schema->getColumn(c);

    ColumnType type = column.getType();
    written += xwrite(fd, &type, sizeof(ColumnType));

    std::string name = column.getName();
    int name_length = name.length();
    const char* name_string = name.data();
    written += xwrite(fd, &name_length, sizeof(int));
    written += xwrite(fd, name_string, name_length);

    size_t offset = schema->getColumnOffset(c);
    written += xwrite(fd, &offset, sizeof(offset));
  }

  return written;
}


Schema*
readSchema(int fd)
{
  assert(fd >= 0);
  
  size_t size;
  xread(fd, &size, sizeof(size_t));

  CustomSchema* schema = new CustomSchema(size);

  int num_columns;
  xread(fd, &num_columns, sizeof(int));

  for (int c = 0; c < num_columns; ++c) {
    ColumnType type;
    xread(fd, &type, sizeof(ColumnType));

    int name_length;
    xread(fd, &name_length, sizeof(int));
    char name[name_length + 1];
    xread(fd, name, name_length);
    name[name_length] = '\0';

    size_t offset;
    xread(fd, &offset, sizeof(offset));

    schema->addColumn(Column(name, type), offset);
  }

  return schema;
}


}  // anonymous namespace


//----------------------------------------------------------------------
// class Row
//----------------------------------------------------------------------

Row::Row(const Schema* schema)
  : schema_(schema)
{
  assert(schema_ != 0);
  data_ = new char[schema_->getSize()];
}


Row::~Row()
{
  delete [] data_;
}


#define ROW_GET(TYPE, OFFSET) \
  (*((TYPE*) (data_ + (OFFSET))))

Value
Row::getValue(const int column_index)
  const
  throw (WrongColumnType)
{
  ColumnType type = schema_->getColumn(column_index).getType();
  size_t offset = schema_->getColumnOffset(column_index);
  switch (type) {
  case TYPE_NONE:
    abort();

  case TYPE_BOOL:
    return Value::make((bool) ROW_GET(int8_t, offset));
		       
  case TYPE_INT_8:
    return Value::make((long) ROW_GET(int8_t, offset));

  case TYPE_INT_16:
    return Value::make((long) ROW_GET(int16_t, offset));
    
  case TYPE_INT_32:
    return Value::make((long) ROW_GET(int32_t, offset));
    
  case TYPE_FLOAT_32:
    return Value::make((double) ROW_GET(float32_t, offset));

  case TYPE_FLOAT_64:
    return Value::make((double) ROW_GET(float64_t, offset));

  case TYPE_COMPLEX_64: 
    return Value::make((std::complex<double>) ROW_GET(complex64_t, offset));

  case TYPE_COMPLEX_128: 
    return Value::make((std::complex<double>) ROW_GET(complex128_t, offset));

  default:
    abort();
  }
}


#define ROW_SET(TYPE, OFFSET, VALUE) \
  *((TYPE*) (data_ + (OFFSET))) = ((TYPE) (VALUE))

void
Row::setValue(const int column_index,
	      const Value& value)
{
  assert(column_index >= 0 && column_index < schema_->getNumColumns());

  ColumnType type = schema_->getColumn(column_index).getType();
  size_t offset = schema_->getColumnOffset(column_index);
  switch (type) {
  case TYPE_NONE:
    abort();

  case TYPE_BOOL:
    ROW_SET(int8_t, offset, value.as_bool());
    break;
		       
  case TYPE_INT_8:
    ROW_SET(int8_t, offset, value.as_long());
    break;

  case TYPE_INT_16:
    ROW_SET(int16_t, offset, value.as_long());
    break;
    
  case TYPE_INT_32:
    ROW_SET(int32_t, offset, value.as_long());
    break;
    
  case TYPE_FLOAT_32:
    ROW_SET(float32_t, offset, value.as_double());
    break;

  case TYPE_FLOAT_64:
    ROW_SET(float64_t, offset, value.as_double());
    break;

  case TYPE_COMPLEX_64:
    ROW_SET(complex64_t, offset, value.as_complex());
    break;

  case TYPE_COMPLEX_128:
    ROW_SET(complex128_t, offset, value.as_complex());
    break;

  default:
    abort();
  }
}  


//----------------------------------------------------------------------
// class Schema
//----------------------------------------------------------------------

Schema::~Schema()
{
}


int
Schema::whichColumn(const std::string& name)
  const
  throw (NoColumn)
{
  int num_columns = columns_.size();
  for (int i = 0; i < num_columns; ++i) 
    if (columns_[i].column_.getName() == name)
      return i;

  throw NoColumn(name);
}


//----------------------------------------------------------------------
// class AutoSchema
//----------------------------------------------------------------------

AutoSchema::AutoSchema()
{
}


AutoSchema::~AutoSchema()
{
}


void
AutoSchema::addColumn(const Column& column)
{
  ColumnRecord record = { column, size_ };
  columns_.push_back(record);
  size_ += getTypeSize(column.getType());
}


//----------------------------------------------------------------------
// class Table
//----------------------------------------------------------------------

Table::~Table()
{
}


//----------------------------------------------------------------------
// class FileTable
//----------------------------------------------------------------------

FileTable*
FileTable::create(const Schema* schema,
		  const std::string& path,
		  mode_t mode)
{
  // Create the file.
  int fd = ::open64(path.c_str(), 
		    O_RDWR | O_CREAT | O_TRUNC | O_LARGEFILE, mode);
  if (fd < 0)
    throw FileError(strerror(errno));

  // Skip forward to leave enough room for the header, then write the
  // schema.
  xseek(fd, sizeof(FileFormatHeader));
  off64_t schema_size = writeSchema(fd, schema);

  // Construct the header info, now that we know how large the schema
  // is.
  FileFormatHeader header;
  header.magic_number_ = file_format_magic_number;
  header.version_number_ = file_format_version_number;
  header.num_rows_ = 0;
  header.first_row_offset_ = sizeof(FileFormatHeader) + schema_size;

  // Write the header at the beginning of the file.
  xseek(fd, 0);
  xwrite(fd, &header, sizeof(header));

  // Close the file.
  close(fd);

  // If there is a metadata file for this path, remove it.
  std::string metadata_path = getMetadataPath(path);
  if (::access(metadata_path.c_str(), X_OK))
    ::unlink(metadata_path.c_str());

  // Now open the newly-created table in the usual way.
  return new FileTable(path, O_RDWR);
}


FileTable*
FileTable::open(const std::string& path,
		const std::string& mode)
{
  int flags;
  if (mode == "r") 
    flags = O_RDONLY;
  else if (mode == "w") 
    flags = O_RDWR;
  else
    throw FileError("unknown mode");

  return new FileTable(path, flags);
}


FileTable::~FileTable()
{
  if (isWritable()) {
    // Build the header.
    FileFormatHeader header;
    header.magic_number_ = file_format_magic_number;
    header.version_number_ = file_format_version_number;
    header.num_rows_ = num_rows_;
    header.first_row_offset_ = first_row_offset_;

    // Write the header.
    xseek(fd_, 0);
    xwrite(fd_, &header, sizeof(header));

    int result = fsync(fd_);
    if (result != 0)
      throw FileError(strerror(errno));
  }

  int result;
  result = close(fd_);
  assert(result == 0);
}


void
FileTable::read(int64_t row_number, 
		Row* row)
{
  assert(row->getSchema() == this->getSchema());
  assert(row_number >= 0 && row_number < num_rows_);

  off64_t offset = first_row_offset_ + row_number * row_size_;
  xseek(fd_, offset);
  xread(fd_, row->getBuffer(), row_size_);
}


int
FileTable::append(const Row* row)
{
  assert(row->getSchema() == this->getSchema());

  if (! isWritable())
    throw NotWritable();

  int64_t row_number = num_rows_;
  off64_t offset = first_row_offset_ + row_number * row_size_;
  xseek(fd_, offset);
  xwrite(fd_, row->getBuffer(), row_size_);

  ++num_rows_;
  return row_number;
}


std::string
FileTable::getMetadata()
  const
{
  std::string path = getMetadataPath(path_);

  // Can we access the metadata file?
  if (::access(path.c_str(), R_OK) != 0)
    // Can't access the metadata file.  Either it doesn't exist or it's
    // inaccessible.  In either case, just return empty metadata.
    return "";

  // Get file information.
  struct stat file_info;
  if (::stat(path.c_str(), &file_info) != 0)
    return "";
  if (file_info.st_size == 0)
    // No metadata.
    return "";

  // Open the metadata file.
  int fd = ::open(path.c_str(), O_RDONLY);
  if (fd == -1) 
    return "";

  // Construct a buffer to hold the metadata.
  std::auto_ptr<Buffer> buffer(new Buffer(file_info.st_size));

  // Read the data.
  xread(fd, buffer->pointer_, file_info.st_size);
  // Clean up.
  ::close(fd);

  return std::string(buffer->pointer_, file_info.st_size);
}


void
FileTable::setMetadata(const std::string& data)
{
  std::string path = getMetadataPath(path_);

  if (data == "") {
    // We don't want a metadata file.  Remove one, if it exists.
    if (::access(path.c_str(), X_OK))
      ::unlink(path.c_str());
    // Don't write.
    return;
  }

  // Create the metadata file.
  int fd = ::open(path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666);
  if (fd == -1) 
    // Could not open the metadata file; fail silently.
    return;

  // Write the metadata.
  xwrite(fd, data.c_str(), data.length());
  // Clean up.
  close(fd);
}


FileTable::FileTable(const std::string& path,
		     int flags)
  : Table(NULL, flags == O_RDWR),
    path_(path)
{
  if (flags != O_RDWR && flags != O_RDONLY)
    // Invalid flags.
    assert(false);

  // Open the file.
  fd_ = ::open64(path.c_str(), flags | O_LARGEFILE);
  if (fd_ < 0) {
    throw FileError(strerror(errno));
  }

  // Read the header.
  FileFormatHeader header;
  xread(fd_, &header, sizeof(header));

  // Check the magic numbers.
  if (header.magic_number_ != file_format_magic_number)
    throw FileError("wrong file format");
  if (header.version_number_ != file_format_version_number)
    throw FileError("wrong file format version");

  // Extract other info from the header.
  num_rows_ = header.num_rows_;
  assert(num_rows_ >= 0);
  first_row_offset_ = header.first_row_offset_;

  // Read the schema.
  schema_ = readSchema(fd_);
  assert(schema_ != NULL);
  row_size_ = schema_->getSize();
}


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

size_t
getTypeSize(ColumnType type)
{
  return type_sizes[(int) type];
}


const char*
getTypeName(ColumnType type)
{
  int i = (int) type;
  if (i >= 0 && i < (int) TYPE_LAST)
    return type_names[i];
  else
    return NULL;
}


ColumnType
getTypeByName(const char* name)
{
  // Try to match the name.
  for (int i = 0; i < (int) TYPE_LAST; ++i)
    if (strcmp(name, type_names[i]) == 0)
      return (ColumnType) i;
  // No match.
  return TYPE_NONE;
}


//----------------------------------------------------------------------

}  // namespace Tables
