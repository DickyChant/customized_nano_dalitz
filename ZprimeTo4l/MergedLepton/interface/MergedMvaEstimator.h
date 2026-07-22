#ifndef MergedMvaEstimator_H
#define MergedMvaEstimator_H 1

#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/ParameterSet/interface/FileInPath.h"
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "CommonTools/MVAUtils/interface/GBRForestTools.h"

#include "ZprimeTo4l/ModifiedHEEP/interface/ModifiedDEtaInSeed.h"
#include "ZprimeTo4l/ModifiedHEEP/interface/ModifiedShowerShape.h"

#include <iostream>
#include <memory>

class MergedMvaEstimator {
public:
  enum mergedElectronVar {
    alphaCalo,
    union5x5covIeIe,
    union5x5dEtaIn,
    union5x5dPhiIn,
    alphaTrack,
    normalizedDParaIn,

    full5x5_sigIeIe = 0,
    full5x5_E1x5oE5x5,
    dEtaInSeed,
    dPhiIn,
    EOverP
  };

  MergedMvaEstimator(const edm::FileInPath& weightsfile, const edm::FileInPath& meanstdfile);
  ~MergedMvaEstimator() {}

  double computeMva(const pat::ElectronRef& el,
                    const ModifiedDEtaInSeed::variables& dEta,
                    const ModifiedShowerShape::variables& ss);
  double computeMva(const pat::ElectronRef& el);

private:
  std::unique_ptr<const GBRForest> gbrForest_;
  std::vector<double> scale_mean_;
  std::vector<double> scale_std_;
};

#endif
