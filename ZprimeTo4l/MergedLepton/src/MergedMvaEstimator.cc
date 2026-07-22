#include "ZprimeTo4l/MergedLepton/interface/MergedMvaEstimator.h"
#include "ZprimeTo4l/MergedLepton/interface/MergedMvaEstimator.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>

MergedMvaEstimator::MergedMvaEstimator(const edm::FileInPath& weightsfile, const edm::FileInPath& meanstdfile) {
  gbrForest_ = createGBRForest(weightsfile);
  std::ifstream fstr(meanstdfile.fullPath());

  if (fstr) {
    std::string line;
    std::getline(fstr, line);
    std::istringstream iss_0(line);
    for (std::string part; std::getline(iss_0,part,' '); scale_mean_.emplace_back(std::stod(part))) {}

    std::getline(fstr, line);
    std::istringstream iss_1(line);
    for (std::string part; std::getline(iss_1,part,' '); scale_std_.emplace_back(std::stod(part))) {}

  } else {
    throw cms::Exception("ConfigError") << "Error: cannot open a file " << meanstdfile.fullPath() << std::endl;
  }

}

double MergedMvaEstimator::computeMva(const pat::ElectronRef& el,
                                      const ModifiedDEtaInSeed::variables& dEta,
                                      const ModifiedShowerShape::variables& ss) {
  const unsigned int nvar = scale_mean_.size();
  float var[nvar];

  const double covEE = ss.covEE;
  const double covEP = ss.covEP;
  const double covPP = ss.covPP;
  const double covMaj = ((covEE + covPP) + std::sqrt((covEE - covPP)*(covEE - covPP) + 4.*covEP*covEP)) / 2.;

  var[mergedElectronVar::alphaCalo] = ss.alpha;
  var[mergedElectronVar::union5x5covIeIe] = ss.covEE;
  var[mergedElectronVar::union5x5dEtaIn] = ss.dEtaInUnion5x5;
  var[mergedElectronVar::union5x5dPhiIn] = ss.dPhiInUnion5x5;
  var[mergedElectronVar::alphaTrack] = dEta.alphaTrack;
  var[mergedElectronVar::normalizedDParaIn] = dEta.normalizedDParaIn;

  for (unsigned int idx = 0; idx < nvar; idx++)
    var[idx] = ( var[idx]-scale_mean_.at(idx) ) / scale_std_.at(idx);

  double rawScore = gbrForest_->GetResponse(var);

  return 1./( 1. + std::exp(-rawScore) ); // return sigmoid
}

double MergedMvaEstimator::computeMva(const pat::ElectronRef& el) {
  const unsigned int nvar = scale_mean_.size();
  float var[nvar];

  var[mergedElectronVar::full5x5_sigIeIe] = el->full5x5_sigmaIetaIeta();
  var[mergedElectronVar::full5x5_E1x5oE5x5] = el->full5x5_e5x5() > 0. ? el->full5x5_e1x5()/el->full5x5_e5x5() : 0.;
  var[mergedElectronVar::dEtaInSeed] = el->deltaEtaSeedClusterTrackAtVtx();
  var[mergedElectronVar::dPhiIn] = el->deltaPhiSuperClusterTrackAtVtx();
  var[mergedElectronVar::EOverP] = el->eSuperClusterOverP();

  for (unsigned int idx = 0; idx < nvar; idx++)
    var[idx] = ( var[idx]-scale_mean_.at(idx) ) / scale_std_.at(idx);

  double rawScore = gbrForest_->GetResponse(var);

  return 1./( 1. + std::exp(-rawScore) ); // return sigmoid
}
