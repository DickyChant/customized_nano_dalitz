#ifndef HDalitzEle_MergedID_HDalitzMergedEstimator_h
#define HDalitzEle_MergedID_HDalitzMergedEstimator_h

// Thin wrapper around the xgboost C API to run the chw1207/HDalitzEle merged-electron
// ID models (multiclass "multi:softprob"). Mirrors HDalitzEle's XGBReader so the scores
// reproduce the original analysis. pat::XGBooster is NOT used because it asserts a single
// output and cannot return the 3-class probability vector.

#include "FWCore/ParameterSet/interface/FileInPath.h"
#include "HDalitzEle/MergedID/interface/HDalitzMergedEstimatorBase.h"

#include <string>
#include <vector>

// forward-declare the xgboost booster handle type (void*) to keep the header light
typedef void* BoosterHandle;

class HDalitzMergedEstimator : public HDalitzMergedEstimatorBase {
public:
  explicit HDalitzMergedEstimator(const edm::FileInPath& modelFile);
  ~HDalitzMergedEstimator() override;

  HDalitzMergedEstimator(const HDalitzMergedEstimator&) = delete;
  HDalitzMergedEstimator& operator=(const HDalitzMergedEstimator&) = delete;

  // number of input features the model expects
  unsigned int nFeatures() const { return nFeatures_; }

  // returns the full softprob vector (one entry per class; class 0 = merged signal)
  std::vector<float> predict(const std::vector<float>& features) const override;

private:
  BoosterHandle booster_ = nullptr;
  unsigned int nFeatures_ = 0;
};

#endif
