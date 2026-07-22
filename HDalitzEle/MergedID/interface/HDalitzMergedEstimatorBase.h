#ifndef HDalitzEle_MergedID_HDalitzMergedEstimatorBase_h
#define HDalitzEle_MergedID_HDalitzMergedEstimatorBase_h

// Common interface so the producer can run either inference backend
// (xgboost c-API in 15_0, ONNXRuntime in 10_6 and 15_0) interchangeably.
// predict() returns the full class-probability vector (class 0 = merged signal).

#include <vector>

class HDalitzMergedEstimatorBase {
public:
  virtual ~HDalitzMergedEstimatorBase() = default;
  virtual std::vector<float> predict(const std::vector<float>& features) const = 0;
};

#endif
