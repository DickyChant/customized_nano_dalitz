#ifndef HDalitzEle_MergedID_HDalitzMergedEstimatorOnnx_h
#define HDalitzEle_MergedID_HDalitzMergedEstimatorOnnx_h

// ONNXRuntime backend for the HDalitzEle merged-electron ID. Portable across CMSSW
// releases (PhysicsTools/ONNXRuntime exists in both 10_6 and 15_0 with an identical
// run() API). Loads the xgboost-exported .onnx model; returns the "probabilities"
// output (3-class softprob; class 0 = merged signal).

#include "FWCore/ParameterSet/interface/FileInPath.h"
#include "HDalitzEle/MergedID/interface/HDalitzMergedEstimatorBase.h"

#include <memory>
#include <string>

namespace cms {
  namespace Ort {
    class ONNXRuntime;
  }
}  // namespace cms

class HDalitzMergedEstimatorOnnx : public HDalitzMergedEstimatorBase {
public:
  explicit HDalitzMergedEstimatorOnnx(const edm::FileInPath& modelFile);
  ~HDalitzMergedEstimatorOnnx() override;

  std::vector<float> predict(const std::vector<float>& features) const override;

private:
  std::unique_ptr<cms::Ort::ONNXRuntime> ort_;
  std::string inputName_ = "input";
  std::string outputName_ = "probabilities";
};

#endif
