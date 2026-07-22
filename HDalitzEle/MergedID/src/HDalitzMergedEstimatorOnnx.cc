#include "HDalitzEle/MergedID/interface/HDalitzMergedEstimatorOnnx.h"
#include "PhysicsTools/ONNXRuntime/interface/ONNXRuntime.h"

#include <cstdint>

using cms::Ort::FloatArrays;
using cms::Ort::ONNXRuntime;

HDalitzMergedEstimatorOnnx::HDalitzMergedEstimatorOnnx(const edm::FileInPath& modelFile)
    : ort_(std::make_unique<ONNXRuntime>(modelFile.fullPath())) {}

HDalitzMergedEstimatorOnnx::~HDalitzMergedEstimatorOnnx() = default;

std::vector<float> HDalitzMergedEstimatorOnnx::predict(const std::vector<float>& features) const {
  FloatArrays inputs{features};  // single-row batch
  const std::vector<std::vector<int64_t>> shapes{{1, static_cast<int64_t>(features.size())}};
  FloatArrays outs = ort_->run({inputName_}, inputs, shapes, {outputName_}, 1);
  return outs.empty() ? std::vector<float>() : outs.front();
}
