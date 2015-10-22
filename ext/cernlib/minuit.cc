//----------------------------------------------------------------------
//
// minuit.cc
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>
#include <pthread.h>
#include <vector>

#include "cernlib.hh"
#include "python.hh"
#include "value.hh"
#include "util.hh"

using namespace Py;

//----------------------------------------------------------------------
// helper classes
//----------------------------------------------------------------------

namespace {

class Minuit
{
public:

  Minuit(bool verbose);
  virtual ~Minuit();

  void parseParameters(Object* parameters_arg);
  void runCommand(const char* command);
  virtual Object* getResults();

protected:

  typedef std::vector<String*> NameList;

  // The names of the parameters.
  NameList parm_names_;

  // The number of parameters.
  int num_parms_;

  // The number of floating parameters.  
  int num_floating_parms_;

  // Map from parameter numbers to floating parameter numbers.
  const static int PARM_FIXED = -1;
  std::vector<int> parm_map_;

  // Symbol table passed to the callback function.  The fixed parameters
  // are initialized when parameters are set.  Floating parameters are
  // set for each evaluation.
  Ref<Dict> symbols_;

  int num_evaluations_;
  virtual double evaluate(Dict* symbols) = 0;

private:

  int output_lun_;
  bool exception_;
  bool exception_dump_;
  static pthread_mutex_t mutex_;

  static void callback(const int* num_parameters, double* derivatives, 
		       double* function_value, const double* parameters, 
		       const int* flag, void* cookie); 

  void callback(const int* num_parameters, double* derivatives, 
		double* function_value, const double* parameters, 
		const int* flag); 

};


Minuit::Minuit(bool verbose)
  : num_parms_(0),
    num_floating_parms_(0),
    symbols_(Dict::New()),
    num_evaluations_(0),
    output_lun_(0),
    exception_(false)
{
  // FIXME: Use thread-local storage to obviate the lock.
  pthread_mutex_lock(&mutex_);

  if (! verbose) {
    // We don't want any output.  Attempt to open /dev/null for Minuit
    // output on LUN 22.
    char path[1024];
    makeFortranString("/dev/null", path, sizeof(path));
    output_lun_ = 22;
    int status;
    open_lun__(&output_lun_, path, &status, strlen(path));
    if (status != 0)
      // Open /dev/null failed.  Use stdout.  Oh well.
      output_lun_ = 0;
  }

  // Initialize Minuit.
  mninit_(&output_lun_, &output_lun_, &output_lun_);

  // FIXME: Close LUN 22.
}


Minuit::~Minuit()
{
  pthread_mutex_unlock(&mutex_);
}


void
Minuit::parseParameters(Object* parameters_arg)
{
  Sequence* parameters = cast<Sequence>(parameters_arg);

  num_parms_ = parameters->Size();
  num_floating_parms_ = 0;
  parm_map_.resize(num_parms_);
  symbols_->Clear();

  // Set up parameters.
  for (int i = 0; i < parameters->Size(); ++i) {
    Ref<Object> parm_obj = parameters->GetItem(i);
    Tuple* parm = cast<Tuple>(parm_obj);

    String* name;
    double initial_value;
    Object* step_size_arg = NULL;
    double bound_lo = 0;
    double bound_hi = 0;
    parm->ParseTuple("Sd|O(dd)", &name, &initial_value, &step_size_arg, 
		     &bound_lo, &bound_hi); 
    double step_size;

    // Store the parameter name.
    parm_names_.push_back(name);

    if (step_size_arg == NULL || step_size_arg == Py_None) {
      // For a fixed parameter, place the value into the symbol map
      // right away.  
      Ref<Float> value = Float::FromDouble(initial_value);
      symbols_->SetItem(name, value);
      // Mark the parameter as fixed.  We won't tell Minuit about it at
      // all. 
      parm_map_[i] = PARM_FIXED;
    }
    else {
      // For a floating parameter, create a Minuit parameter.  These are
      // one-indexed. 
      int parm_number = ++num_floating_parms_;
      char parm_name[10];
      makeFortranString(name->AsString(), parm_name, sizeof(parm_name));
      step_size = (float) step_size_arg->FloatAsDouble();
      int error_code;
      mnparm_(&parm_number, parm_name, &initial_value, &step_size, 
	      &bound_lo, &bound_hi, &error_code, sizeof(parm_name));
      if (error_code != 0)
	throw Exception(PyExc_RuntimeError,
			"Minuit call MNPARM failed with code %d", 
			error_code);
      // Note the Minuit parameter number corresponding to this
      // parameter.
      parm_map_[i] = parm_number;
    }
  }
}


void
Minuit::runCommand(const char* command)
{
  int error_code;
  mncomd_(&callback, command, &error_code, this, strlen(command));

  // Was a Python exception thrown while evaluating the function?
  if (exception_)
    // Yes.  Propagate it.
    throw Exception();
}


Object*
Minuit::getResults()
{
  Ref<Object> result_class = import("hep.cernlib.minuit", "Result");
  Callable* result_ctor = cast<Callable>(result_class);
  Ref<Object> result = result_ctor->CallFunctionObjArgs(NULL);

  // Store minimization status.
  double minimum;
  double unused1;
  int unused2;
  int status;
  mnstat_(&minimum, &unused1, &unused1, &unused2, &unused2, &status);
  Ref<Float> minimum_obj = Float::FromDouble(minimum);
  result->SetAttrString("minimum", minimum_obj);
  Ref<Int> status_obj = Int::FromLong(status);
  result->SetAttrString("minuit_status", status_obj);

  // Store parameter values and errors.
  Ref<Dict> values = Dict::New();
  Ref<Dict> errors = Dict::New();
  for (int i = 0; i < num_parms_; ++i) {
    int parm_number = parm_map_[i];
    double value;
    double error;

    if (parm_number == PARM_FIXED) {
      // A fixed parameter.  Retrieve the value from the symbol map.
      Ref<Object> value_obj = symbols_->GetItem(parm_names_[i]);
      value = value_obj->FloatAsDouble();
      error = 0;
    }
    else if (0 < parm_number && parm_number <= num_floating_parms_) {
      // A floating parmameter.  Get the value and error from Minuit. 
      char parm_name[10];
      double unused1;
      int unused2;
      mnpout_(&parm_number, parm_name, &value, &error, &unused1, 
	      &unused1, &unused2, sizeof(parm_name));
    }
    else
      assert(false);

    Ref<Float> value_obj = Float::FromDouble(value);
    values->SetItem(parm_names_[i], value_obj);
    Ref<Float> error_obj = Float::FromDouble(error);
    errors->SetItem(parm_names_[i], error_obj);
  }
  result->SetAttrString("values", values);
  result->SetAttrString("errors", errors);

  // Store the number of evaluations.
  Ref<Int> num_evaluations = Int::FromLong(num_evaluations_);
  result->SetAttrString("num_evaluations", num_evaluations);

  // Retrieve the covariance matrix from Minuit.
  double covariances[sqr(num_floating_parms_)];
  memset(covariances, 0, sizeof(covariances));
  mnemat_(covariances, &num_floating_parms_);
  // Convert it to a Python object.
  Ref<Tuple> covariance_matrix = Tuple::New(num_floating_parms_);
  for (int i = 0; i < num_floating_parms_; ++i) {
    Ref<Tuple> covariance_row = Tuple::New(num_floating_parms_);
    for (int j = 0; j < num_floating_parms_; ++j) {
      double val = covariances[i * num_floating_parms_ + j];
      Ref<Float> val_obj = Float::FromDouble(val);
      covariance_row->InitializeItem(j, val_obj);
    }
    covariance_matrix->InitializeItem(i, covariance_row);
  }
  result->SetAttrString("covariance_matrix", covariance_matrix);

  // All done.
  return result.release();
}


pthread_mutex_t
Minuit::mutex_ = PTHREAD_MUTEX_INITIALIZER;


void
Minuit::callback(const int* num_parameters,
		 double* derivatives,
		 double* function_value,
		 const double* parameters,
		 const int* flag,
		 void* cookie)
{
  Minuit* this_ = reinterpret_cast<Minuit*>(cookie);

  // Has an exception occurred already?
  if (this_->exception_) {
    // Yes.  
    if (! this_->exception_dump_) {
      // Display the parameter values at the exception.
      std::cerr << "Minuit: An exception occurred while evaluating.\n";
      std::cerr << "Parameter values:\n";
      for (int i = 0; i < this_->num_parms_; ++i) {
	int parm_number = this_->parm_map_[i];
	// Skip fixed parameters.
	if (parm_number == PARM_FIXED) 
	  continue;
	// Dump the parameter value.
	double value = parameters[parm_number - 1];
	std::cerr << "  " << this_->parm_names_[i]->AsString() << " = " 
		  << value << "\n";
      }
      std::cerr << "\n";
      this_->exception_dump_ = true;
    }

    // Don't evaluate the function any more.  Keep returning zero, in
    // hope that Minuit will give up soon.
    *function_value = 0;
    return;
  }

  // FIXME: There are some problems (?) throwing an exception through
  // Minuit.  We have to catch the exception here instead.
  try {
    this_->callback(num_parameters, derivatives, function_value, 
		    parameters, flag);
  }
  catch (Exception exception) {
    // Flag the exception and return to Minuit.  The Python exception
    // state remains untouched; the caller of Minuit can pick it up and
    // propagate the exception.
    this_->exception_ = true;
    this_->exception_dump_ = false;
    *function_value = 0;
  }
}


inline void
Minuit::callback(const int* num_parameters,
		 double* derivatives,
		 double* function_value,
		 const double* parameters,
		 const int* flag)
{
  if (*flag == 2)
    throw Exception(PyExc_NotImplementedError, 
		    "computation of derivatives not supported");

  // Start by adding parameter values.
  for (unsigned i = 0; i < parm_names_.size(); ++i) {
    int parm_number = parm_map_[i];
    // Skip fixed parameters.
    if (parm_number == PARM_FIXED)
      continue;

    // Set the parameter name and value in the dictionary.
    Ref<Float> parm_value = Float::FromDouble(parameters[parm_number - 1]);
    symbols_->SetItem(parm_names_[i], parm_value);
  }

  *function_value = evaluate(symbols_);
  ++num_evaluations_;
}


//----------------------------------------------------------------------

class Minimizer
  : public Minuit
{
public:

  Minimizer(Callable* function, bool verbose=false, bool negate=false);
  virtual double evaluate(Dict* symbols);

protected:

  Callable* const function_;
  bool negate_;

};


Minimizer::Minimizer(Callable* function,
		     bool verbose,
		     bool negate)
  : Minuit(verbose),
    function_(function),
    negate_(negate)
{
}


double
Minimizer::evaluate(Dict* symbols)
{
  // FIXME: Optimize PyExpr evaluate case?
  Ref<Object> result_obj = function_->Call(NULL, symbols);
  double result = result_obj->FloatAsDouble();
  if (negate_)
    result = -result;
  return result;
}


//----------------------------------------------------------------------

class MaximumLikelihoodFit
  : public Minuit
{
public:

  MaximumLikelihoodFit(Callable* likelihood_fn,
		       Object* sampels, bool verbose=false);
  virtual ~MaximumLikelihoodFit();

  void setNormalizationRange(Sequence* normalization_range);
  void setExtendedFunction(Callable* extended_fn);

  virtual double evaluate(Dict* parameters);

protected:

  Callable* getLikelihoodFunction(Dict* parameters, double* normalization);

  Callable* const likelihood_fn_;
  Object* samples_;
  Sequence* normalization_range_;
  Callable* extended_fn_;  

};


MaximumLikelihoodFit::MaximumLikelihoodFit(Callable* likelihood_fn,
					   Object* samples,
					   bool verbose)
  : Minuit(verbose),
    likelihood_fn_(likelihood_fn),
    samples_(samples),
    normalization_range_(NULL),
    extended_fn_(NULL)
{
}


MaximumLikelihoodFit::~MaximumLikelihoodFit()
{
}


void
MaximumLikelihoodFit::setNormalizationRange(Sequence* normalization_range)
{
  assert(normalization_range != NULL);
  normalization_range_ = normalization_range;
}


void
MaximumLikelihoodFit::setExtendedFunction(Callable* extended_fn)
{
  assert(extended_fn != NULL);
  extended_fn_ = extended_fn;
}


double 
MaximumLikelihoodFit::evaluate(Dict* parameters)
{
  double log_likelihood = 0;
  
  // First, evaluate the extended function, if any.
  if (extended_fn_ != NULL) {
    Ref<Object> value = 
      extended_fn_->CallFunctionObjArgs(parameters, NULL);
    log_likelihood += value->FloatAsDouble();
  }

  // Get the likelihood function with the parameters substituted,
  // normalized if necessary. 
  double normalization;
  Ref<Callable> likelihood_fn = 
    getLikelihoodFunction(parameters, &normalization);
  // Compile it.
  static Callable* compile =
    cast<Callable>(import("hep.expr", "compile"));
  Ref<Callable> likelihood = 
    compile->CallFunctionObjArgs(likelihood_fn, NULL);

  Ref<Object> evaluate_obj = likelihood->GetAttrString("evaluate");
  Callable* evaluate = cast<Callable>(evaluate_obj);

  // Loop over samples.
  Ref<Iter> iter = samples_->GetIter();
  int num_samples = 0;
  for (Ref<Object> sample = iter->Next();
       sample != NULL;
       sample = iter->Next()) {
    Ref<Object> value_obj = evaluate->CallFunctionObjArgs(sample, NULL);
    double value = value_obj->FloatAsDouble();
    // Check the range of the likelihood function.
    if (value < 0) {
      Ref<String> parameters_str = parameters->Str();
      Ref<String> sample_str = sample->Str();
      throw Exception(PyExc_ValueError, 
	"negative likelihood value for parameters %s, sample %s",
	 parameters_str->AsString(), sample_str->AsString());
    }
    else if (value == 0)
      // FIXME: Are you sure you want to do this?
      log_likelihood += 1e+300;
    else 
      log_likelihood -= log(value);
    ++num_samples;
  }

  // Correct for normalization.
  log_likelihood -= num_samples * log(normalization);

  // All done.
  return log_likelihood;
}


Callable* 
MaximumLikelihoodFit::getLikelihoodFunction(Dict* parameters,
					    double* normalization)
{
  // Substitute the parameters into the likelihood function.
  static Ref<Callable> substitute = 
    cast<Callable>(import("hep.expr", "substitute"));
  Ref<Tuple> args = Tuple::New(1);
  args->InitializeItem(0, likelihood_fn_);
  Ref<Object> likelihood_fn_obj = 
    substitute->Call(args, parameters);
  Callable* likelihood_fn = cast<Callable>(likelihood_fn_obj);

  // Compute normalization, if necessary.
  if (normalization_range_ != NULL &&
      normalization_range_->Size() > 0) {
    int integration_vars = normalization_range_->Size();

    std::vector<IntegrationRange> integration_range;
    for (int v = 0; v < integration_vars; ++v) {
      Ref<Object> range_obj = normalization_range_->GetItem(v);
      Tuple* range = cast<Tuple>(range_obj);
      String* var_name;
      Object* lo_expr;
      Object* hi_expr;
      range->ParseTuple("SOO", &var_name, &lo_expr, &hi_expr);
      Ref<Object> lo_obj = 
	cast<Callable>(lo_expr)->CallFunction(NULL, parameters);
      double lo = lo_obj->FloatAsDouble();
      Ref<Object> hi_obj =
	cast<Callable>(hi_expr)->CallFunction(NULL, parameters);
      double hi = hi_obj->FloatAsDouble();
      integration_range.push_back(IntegrationRange(var_name, lo, hi));
    }

    // Compile the integrand.
    static Callable* compile =
      cast<Callable>(import("hep.expr", "compile"));
    Ref<Callable> likelihood = 
      compile->CallFunctionObjArgs(likelihood_fn, NULL);
    // Integrate.
    double integral = integrate(likelihood, integration_range);
    if (integral <= 0)
      throw Exception(PyExc_ValueError, 
		      "nonpositive integral of likelihood function");
    *normalization = 1 / integral;
  }

  else
    // No normalization needed.
    *normalization = 1;

  likelihood_fn_obj.release();
  return likelihood_fn;
}


}  // anonymous namespace

//----------------------------------------------------------------------
// Python functions
//----------------------------------------------------------------------

Object*
function_minuit_minimize(PyObject* /* self */,
			 Arg* args)
try {
  Object* function_arg;
  Object* parameters_arg;
  Object* verbose_arg = (Object*) Py_False;
  Object* do_minos_arg = (Object*) Py_False;
  Object* negate_arg = (Object*) Py_False;
  args->ParseTuple("OO|OOO", &function_arg, &parameters_arg, 
		   &verbose_arg, &do_minos_arg, &negate_arg);
  Callable* function = cast<Callable>(function_arg);
  bool verbose = verbose_arg->IsTrue();
  bool do_minos = do_minos_arg->IsTrue();
  bool negate = negate_arg->IsTrue();

  // Initialize Minuit.
  Minimizer minuit(function, verbose, negate);
  minuit.parseParameters(parameters_arg);
  // Do the actual minimization.
  minuit.runCommand("minimize");
  // Use MINOS to compute the covariance matrix.
  if (do_minos)
    minuit.runCommand("minos");
  // Extract the results.
  Ref<Object> results = minuit.getResults();
  // Done with Minuit.
  minuit.runCommand("end");

  return results.release();
}
catch (Exception) {
  return NULL;
}


Object*
function_minuit_maximumLikelihoodFit(PyObject* /* self */,
				     Arg* args)
try {
  Object* likelihood;
  Object* parameters;
  Object* samples;
  Object* normalization_range = NULL;
  Object* extended_fn = NULL;
  Object* verbose_arg = (Object*) Py_False;
  Object* do_minos_arg = (Object*) Py_False;
  // FIXME: Support keyword arguments.
  args->ParseTuple("OOO|OOOO", &likelihood, &parameters, &samples, 
		   &normalization_range, &extended_fn, &verbose_arg,
		   &do_minos_arg);
  bool verbose = verbose_arg->IsTrue();
  bool do_minos = do_minos_arg->IsTrue();

  // Initialize Minuit.
  MaximumLikelihoodFit fit(cast<Callable>(likelihood), samples, verbose);
  fit.parseParameters(parameters);

  if (normalization_range != NULL && normalization_range != Py_None)
    fit.setNormalizationRange(cast<Sequence>(normalization_range));
  if (extended_fn != NULL && extended_fn != Py_None)
    fit.setExtendedFunction(cast<Callable>(extended_fn));

  // Do the actual fit.
  fit.runCommand("minimize");
  // Use MINOS to compute the covariance matrix.
  if (do_minos)
    fit.runCommand("minos");
  // Extract the results.
  Ref<Object> results = fit.getResults();
  // Done with Minuit.
  fit.runCommand("end");

  return results.release();
}
catch (Exception) {
  return NULL;
}
