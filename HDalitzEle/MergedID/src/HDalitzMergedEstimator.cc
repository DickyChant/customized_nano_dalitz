#include "HDalitzEle/MergedID/interface/HDalitzMergedEstimator.h"

#ifdef HDALITZ_HAS_XGBOOST
#include "FWCore/Utilities/interface/Exception.h"

#include <xgboost/c_api.h>

#include <limits>

namespace {
  void check(int rc) {
    if (rc != 0)
      throw cms::Exception("HDalitzMergedEstimator") << "xgboost error: " << XGBGetLastError();
  }
}  // namespace

HDalitzMergedEstimator::HDalitzMergedEstimator(const edm::FileInPath& modelFile) {
  check(XGBoosterCreate(nullptr, 0, &booster_));
  check(XGBoosterSetParam(booster_, "nthread", "1"));
  check(XGBoosterLoadModel(booster_, modelFile.fullPath().c_str()));
  bst_ulong nf = 0;
  check(XGBoosterGetNumFeature(booster_, &nf));
  nFeatures_ = static_cast<unsigned int>(nf);
}

HDalitzMergedEstimator::~HDalitzMergedEstimator() {
  if (booster_)
    XGBoosterFree(booster_);
}

std::vector<float> HDalitzMergedEstimator::predict(const std::vector<float>& features) const {
  std::vector<float> result;
  if (features.size() != nFeatures_)
    throw cms::Exception("HDalitzMergedEstimator")
        << "feature size mismatch: got " << features.size() << ", model expects " << nFeatures_;

  DMatrixHandle dvalues = nullptr;
  check(XGDMatrixCreateFromMat(features.data(), 1, features.size(), std::numeric_limits<float>::infinity(), &dvalues));

  // strict_shape:true -> out_shape = {n_samples, n_classes}; type 0 = normal margin/softprob
  const char* config = R"({"training":false,"type":0,"iteration_begin":0,"iteration_end":0,"strict_shape":true})";
  bst_ulong out_len = 0;
  const bst_ulong* out_shape = nullptr;
  const float* out = nullptr;
  int rc = XGBoosterPredictFromDMatrix(booster_, dvalues, config, &out_shape, &out_len, &out);
  if (rc == 0 && out != nullptr)
    result.assign(out, out + out_len);

  XGDMatrixFree(dvalues);
  if (rc != 0)
    throw cms::Exception("HDalitzMergedEstimator") << "predict failed: " << XGBGetLastError();
  return result;
}

#endif  // HDALITZ_HAS_XGBOOST
