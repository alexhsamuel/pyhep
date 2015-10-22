//------------------------------------------------------------*- c++ -*-
//
// root.i
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

// SWIG interface file for Root libraries.

// -*- c++ -*-

%module root
%{
#include "TROOT.h"
#include "TKey.h"
#include "TDirectory.h"
#include "TFile.h"
#include "TLeaf.h"
#include "TLeafD.h"
#include "TLeafF.h"
#include "TLeafI.h"
#include "TList.h"
#include "TObject.h"
#include "TTree.h"
#include "TH1.h"
#include "TH2.h"
#include "TH3.h"
#include "TAxis.h"

class IndexError 
{
public:
  IndexError(int index) : index_(index) {};
  const int index_;
};

class StopIteration {};

%}

%inline %{
long 
getPointerValue(void* ptr) 
{
   return (long) ptr;
}
%}

%except(python) {
  try {
    $function
  }
  catch (IndexError e) {
    PyErr_Format(PyExc_IndexError, "%d", e.index_);
    return NULL;
  }
  catch (StopIteration) {
    PyErr_SetString(PyExc_StopIteration, "end of iterator");
    return NULL;
  }
}


class TObject
{
public:

  bool IsZombie() const;
  virtual const char* ClassName() const;
  virtual const char* GetName() const;
  virtual const char* GetTitle() const;
  virtual bool InheritsFrom(const char *classname) const;
  virtual void Print(const char* option) const;
  virtual int Write(const char* name=0, int option=0, int bufsize=0);

};


class TNamed
  : public TObject
{
public:

  virtual void SetName(const char* name);
  virtual void SetTitle(const char* title);

};


%pragma no_default

class TIterator
  : public TObject
{
public:

  virtual TObject* Next();

};

%addmethods TIterator {
  TIterator* __iter__() 
  {
    return self;
  };


  TObject* next()
  {
    TObject* object = self->Next();
    if (object == NULL)
      throw StopIteration();
    else
      return object;
  };
};



class TClass
  : public TObject
{
public:

  bool InheritsFrom(const char* cl) const;

};


class TKey
  : public TNamed
{
public:

  const char* GetClassName() const;
  short GetCycle() const;
  virtual TClass* IsA() const;

};


class TDirectory
  : public TNamed
{
public:

  virtual bool cd();
  virtual void Delete(const char* namecycle);
  virtual TObject* Get(const char* namecycle);
  TFile* GetFile() const;
  TKey* GetKey(const char* name, short cycle=9999);
  TList* GetList() const;
  TList* GetListOfKeys() const;
  TObject* GetMother() const;
  const char* GetPath() const;
  virtual TDirectory* mkdir(const char* name, const char* title);
  void Purge(short nKeep);
  
};


class TFile
  : public TDirectory
{
public:

  TFile(const char* fname, 
	char* option="", 
	const char* ftitle="", 
	int compress=1);

  virtual bool cd(const char *path = 0);
  virtual void Close(char* option="");
  virtual int Write(const char* name=0, int opt=0, int bufsiz=0);

};


class TList
  : public TObject
{
public:

  virtual int GetSize() const;
  virtual TObject* At(int idx) const;

};


%addmethods TList {
  int __len__() 
  {
    return self->GetSize();
  };


  TObject* __getitem__(int idx) 
  {
    if (idx < 0 || idx >= self->GetSize()) 
      throw IndexError(idx);
    else
      return self->At(idx);
  };
};



class TTree
  : public TObject
{
public:

  virtual int GetEntry(int entry=0, int getall=0);
  virtual double GetEntries() const;
  virtual TIterator* GetIteratorOnAllLeaves();
  virtual void Print();

};


class TLeaf
  : public TObject
{
public:
  
  virtual void SetAddress(void* add=0);

};

%addmethods TLeaf {
  void SetAddressInt(int add=0) 
  {
    self->SetAddress((void*) add);
  };
};


class TLeafD
  : public TLeaf
{
};


class TLeafF
  : public TLeaf
{
};


class TLeafI
  : public TLeaf
{
};


class TH1
  : public TNamed
{
public:

  virtual TAxis* GetXaxis();
  virtual TAxis* GetYaxis();
  virtual TAxis* GetZaxis();
  virtual double GetBinContent(int bin);
  virtual double GetBinError(int bin);
  virtual double GetEntries();
  virtual void SetBinContent(int bin, double content);
  virtual void SetBinError(int bin, double error);
  virtual void SetEntries(double entries);

};


class TH1F 
  : public TH1
{
public:

  TH1F(const char* name, const char* title, int nbinsx, 
       double xlow, double xup);

};


class TH1D
  : public TH1
{
public:

  TH1D(const char* name, const char* title, int nbinsx, 
       double xlow, double xup);

};


class TH1C
  : public TH1
{
public:

  TH1C(const char* name, const char* title, int nbinsx, 
       double xlow, double xup);

};


class TH1S
  : public TH1
{
public:

  TH1S(const char* name, const char* title, int nbinsx, 
       double xlow, double xup);

};


class TH2
  : public TH1
{
public:

  virtual double GetBinContent(int binx, int biny);
  virtual double GetBinError(int binx, int biny);
  virtual void SetBinContent(int binx, int biny, double content);
  virtual void SetBinError(int binx, int biny, double error);

};


class TH2C
  : public TH2
{
public:

  TH2C(const char* name, const char* title, int nbinsx, double xlow,
       double xup, int nbinsy, double ylow, double yup);

};


class TH2D
  : public TH2
{
public:

  TH2D(const char* name, const char* title, int nbinsx, double xlow,
       double xup, int nbinsy, double ylow, double yup);

};


class TH2F
  : public TH2
{
public:

  TH2F(const char* name, const char* title, int nbinsx, double xlow,
       double xup, int nbinsy, double ylow, double yup);

};


class TH2S
  : public TH2
{
public:

  TH2S(const char* name, const char* title, int nbinsx, double xlow,
       double xup, int nbinsy, double ylow, double yup);

};


class TH3
  : public TH1
{
};


class TAxis
  : public TObject
{
public:

  int GetNbins();
  double GetXmin();
  double GetXmax();

};
