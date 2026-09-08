// Ports the chw1207/HDalitzEle merged-electron ID (H->gamma* gamma->ee gamma) into a
// CMSSW producer that attaches the XGBoost discriminant to electrons as ValueMaps.
//
// The ID has two flavours, selected per electron by the presence of a second ("sub") GSF
// track associated to the reco electron:
//   * Merged-2Gsf (a valid sub-GSF found): 22 features incl. gsfPtRatio, gsfDeltaR, gsfRelPtRatio
//   * Merged-1Gsf (no sub-GSF):            20 features (drops gsfPtRatio, gsfDeltaR)
// each split EB (|SCeta|<1.479) / EE, giving 4 models. Models are xgboost multi:softprob
// with 3 classes [merged-signal(0), DYJets(1), QCD(2)]; the discriminant is softprob[0].
//
// The main+sub GSF-track association reproduces HDalitzEle's gsf::TrkEleAssociation:
// reduced GSF tracks are grouped into contiguous chunks delimited by each electron's main
// GSF track; the sub track is the opposite-charge, PV-compatible (IP cuts), non-conversion
// track with the smallest dR to the main one.

#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/isFinite.h"
#include "FWCore/Utilities/interface/Exception.h"

#include "DataFormats/Common/interface/ValueMap.h"
#include "DataFormats/Common/interface/View.h"
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/GsfTrackReco/interface/GsfTrack.h"
#include "DataFormats/GsfTrackReco/interface/GsfTrackFwd.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/Math/interface/LorentzVector.h"

#include "HDalitzEle/MergedID/interface/HDalitzMergedEstimatorBase.h"
#include "HDalitzEle/MergedID/interface/HDalitzMergedEstimatorOnnx.h"
#ifdef HDALITZ_HAS_XGBOOST
#include "HDalitzEle/MergedID/interface/HDalitzMergedEstimator.h"
#endif

#include <algorithm>
#include <memory>
#include <vector>

class HDalitzMergedIDProducer : public edm::stream::EDProducer<> {
public:
  explicit HDalitzMergedIDProducer(const edm::ParameterSet&);
  ~HDalitzMergedIDProducer() override = default;

private:
  void produce(edm::Event&, const edm::EventSetup&) override;

  template <typename T>
  void writeValueMap(edm::Event&,
                     const edm::Handle<edm::View<pat::Electron>>&,
                     const std::vector<T>&,
                     const std::string&);

  const edm::EDGetTokenT<edm::View<pat::Electron>> eleToken_;
  const edm::EDGetTokenT<edm::View<reco::GsfTrack>> gsfToken_;
  const edm::EDGetTokenT<double> rhoToken_;
  const edm::EDGetTokenT<reco::VertexCollection> vtxToken_;

  const double m1EBWP_, m1EEWP_, m2EBWP_, m2EEWP_;

  static std::unique_ptr<HDalitzMergedEstimatorBase> makeEstimator(const std::string& backend,
                                                                   const edm::FileInPath& f);

  std::unique_ptr<HDalitzMergedEstimatorBase> m1EB_, m1EE_, m2EB_, m2EE_;

  static constexpr float kEleMass = 0.000510998950f;
  static constexpr float kSentinel = -999.f;
};

HDalitzMergedIDProducer::HDalitzMergedIDProducer(const edm::ParameterSet& cfg)
    : eleToken_(consumes<edm::View<pat::Electron>>(cfg.getParameter<edm::InputTag>("srcEle"))),
      gsfToken_(consumes<edm::View<reco::GsfTrack>>(cfg.getParameter<edm::InputTag>("srcGsfTracks"))),
      rhoToken_(consumes<double>(cfg.getParameter<edm::InputTag>("srcRho"))),
      vtxToken_(consumes<reco::VertexCollection>(cfg.getParameter<edm::InputTag>("srcVertices"))),
      m1EBWP_(cfg.getParameter<double>("m1EBWPTight")),
      m1EEWP_(cfg.getParameter<double>("m1EEWPTight")),
      m2EBWP_(cfg.getParameter<double>("m2EBWPTight")),
      m2EEWP_(cfg.getParameter<double>("m2EEWPTight")) {
  const std::string backend = cfg.getParameter<std::string>("backend");  // "onnx" | "xgboost"
  m1EB_ = makeEstimator(backend, cfg.getParameter<edm::FileInPath>("modelM1EB"));
  m1EE_ = makeEstimator(backend, cfg.getParameter<edm::FileInPath>("modelM1EE"));
  m2EB_ = makeEstimator(backend, cfg.getParameter<edm::FileInPath>("modelM2EB"));
  m2EE_ = makeEstimator(backend, cfg.getParameter<edm::FileInPath>("modelM2EE"));
  produces<edm::ValueMap<float>>("hdalitzMergedIDScore");
  produces<edm::ValueMap<int>>("hdalitzMergedNGsf");
  produces<edm::ValueMap<int>>("hdalitzMergedCategory");   // 0 M1EB, 1 M1EE, 2 M2EB, 3 M2EE
  produces<edm::ValueMap<int>>("hdalitzMergedWPTight");

  // --- main (the electron's own) and additional/sub GSF track ---
  // The downstream H->ee gamma analysis rebuilds the merged electron from BOTH GSF tracks:
  // its mass is the di-track invariant mass, and the track-level d0/dz/charge/hit quantities
  // drive the PV / opposite-sign / non-conversion cuts and the per-track scale factors.
  // Publishing them here removes the need to re-associate tracks to electrons downstream.
  for (const char* l : {"MainGsfPt", "MainGsfEta", "MainGsfPhi", "MainGsfD0", "MainGsfDz",
                        "AddGsfPt", "AddGsfEta", "AddGsfPhi", "AddGsfD0", "AddGsfDz",
                        "GsfPtRatio", "GsfDeltaR", "GsfRelPtRatio", "GsfPtSum",
                        "DiTrkPt", "DiTrkMass"})
    produces<edm::ValueMap<float>>(std::string("hdalitz") + l);
  for (const char* l : {"MainGsfCharge", "MainGsfMissHits", "MainGsfLostHits",
                        "MainGsfPixelHits", "MainGsfLayers",
                        "AddGsfCharge", "AddGsfMissHits", "AddGsfLostHits",
                        "AddGsfPixelHits", "AddGsfLayers", "HasAddGsf"})
    produces<edm::ValueMap<int>>(std::string("hdalitz") + l);
}

std::unique_ptr<HDalitzMergedEstimatorBase> HDalitzMergedIDProducer::makeEstimator(
    const std::string& backend, const edm::FileInPath& f) {
  if (backend == "onnx")
    return std::make_unique<HDalitzMergedEstimatorOnnx>(f);
#ifdef HDALITZ_HAS_XGBOOST
  if (backend == "xgboost")
    return std::make_unique<HDalitzMergedEstimator>(f);
#endif
  throw cms::Exception("HDalitzMergedIDProducer")
      << "unknown/unavailable backend '" << backend << "' -- this build supports: onnx"
#ifdef HDALITZ_HAS_XGBOOST
         ", xgboost"
#endif
         ".";
}

void HDalitzMergedIDProducer::produce(edm::Event& iEvent, const edm::EventSetup&) {
  auto eleHandle = iEvent.getHandle(eleToken_);
  auto gsfHandle = iEvent.getHandle(gsfToken_);
  const double rho = iEvent.get(rhoToken_);
  const auto& vtxs = iEvent.get(vtxToken_);

  const size_t nEle = eleHandle->size();
  std::vector<float> outScore(nEle, kSentinel);
  std::vector<int> outNGsf(nEle, 0), outCat(nEle, -1), outWP(nEle, 0);

  // main/additional GSF track quantities (kSentinel / -1 when the track does not exist)
  std::vector<float> oMPt(nEle, kSentinel), oMEta(nEle, kSentinel), oMPhi(nEle, kSentinel),
      oMD0(nEle, kSentinel), oMDz(nEle, kSentinel), oAPt(nEle, kSentinel), oAEta(nEle, kSentinel),
      oAPhi(nEle, kSentinel), oAD0(nEle, kSentinel), oADz(nEle, kSentinel),
      oPtRatio(nEle, kSentinel), oDeltaR(nEle, kSentinel), oRelPtRatio(nEle, kSentinel),
      oPtSum(nEle, kSentinel), oDiTrkPt(nEle, kSentinel), oDiTrkMass(nEle, kSentinel);
  std::vector<int> oMCharge(nEle, 0), oMMiss(nEle, -1), oMLost(nEle, -1), oMPix(nEle, -1),
      oMLayers(nEle, -1), oACharge(nEle, 0), oAMiss(nEle, -1), oALost(nEle, -1), oAPix(nEle, -1),
      oALayers(nEle, -1), oHasAdd(nEle, 0);

  // primary vertex (fall back to origin if none) -- used for track d0/dz, matching ggNtuplizer
  const reco::Vertex::Point pv = vtxs.empty() ? reco::Vertex::Point(0, 0, 0) : vtxs.front().position();

  // per-GSF-track quantities (over reducedGsfTracks), same accessors as ggNtuplizer
  const size_t nGsf = gsfHandle->size();
  std::vector<float> gD0(nGsf), gDz(nGsf), gEta(nGsf), gPhi(nGsf), gPt(nGsf);
  std::vector<int> gCharge(nGsf), gMiss(nGsf), gLost(nGsf), gPix(nGsf), gLayers(nGsf);
  for (size_t j = 0; j < nGsf; ++j) {
    const auto& g = (*gsfHandle)[j];
    gD0[j] = g.dxy(pv);
    gDz[j] = g.dz(pv);
    gEta[j] = g.eta();
    gPhi[j] = g.phi();
    gPt[j] = g.pt();
    gCharge[j] = g.charge();
    gMiss[j] = g.hitPattern().numberOfAllHits(reco::HitPattern::MISSING_INNER_HITS);
    gLost[j] = g.hitPattern().numberOfLostHits(reco::HitPattern::MISSING_INNER_HITS);
    gPix[j] = g.hitPattern().numberOfValidPixelHits();
    gLayers[j] = g.hitPattern().trackerLayersWithMeasurement();
  }

  // main GSF index for each electron (the electron's own GSF track inside reducedGsfTracks)
  std::vector<int> mainIdx(nEle, -1);
  for (size_t i = 0; i < nEle; ++i) {
    const auto& gt = (*eleHandle)[i].gsfTrack();
    if (gt.isNonnull() && gt.id() == gsfHandle.id() && gt.key() < nGsf) {
      mainIdx[i] = static_cast<int>(gt.key());
    } else if (gt.isNonnull()) {  // fallback: match by (d0,dz) as in HDalitzEle
      const float eD0 = gt->dxy(pv), eDz = gt->dz(pv);
      for (size_t j = 0; j < nGsf; ++j)
        if (gD0[j] == eD0 && gDz[j] == eDz) {
          mainIdx[i] = static_cast<int>(j);
          break;
        }
    }
  }

  // sorted list of main indices -> chunk boundaries (gsf::TrkEleAssociation)
  std::vector<int> sortedMain;
  for (int m : mainIdx)
    if (m >= 0)
      sortedMain.push_back(m);
  std::sort(sortedMain.begin(), sortedMain.end());

  for (size_t i = 0; i < nEle; ++i) {
    const pat::Electron& ele = (*eleHandle)[i];
    const int m = mainIdx[i];
    if (m < 0)
      continue;

    // chunk = [m, next main index) : the ambiguous GSF tracks associated to this electron
    int nextMain = static_cast<int>(nGsf);
    for (int s : sortedMain)
      if (s > m) {
        nextMain = s;
        break;
      }
    const int nGsfMatch = nextMain - m;
    outNGsf[i] = nGsfMatch;

    const float scEta = ele.superCluster()->eta();
    const float scRawEn = ele.superCluster()->rawEnergy();
    const bool isEB = std::abs(scEta) < 1.479f;

    // find the sub GSF track (gsf::FindSubGSF_dRMinWithCuts)
    int subIdx = -1;
    float bestDR = 999.f;
    for (int j = m + 1; j < nextMain; ++j) {
      if (gCharge[m] * gCharge[j] > 0)
        continue;
      const bool fromPV = isEB ? (std::abs(gD0[j]) < 0.02f && std::abs(gDz[j]) < 0.1f)
                               : (std::abs(gD0[j]) < 0.05f && std::abs(gDz[j]) < 0.2f);
      if (!fromPV || gMiss[j] > 0)
        continue;
      const float dR = reco::deltaR(gEta[m], gPhi[m], gEta[j], gPhi[j]);
      if (dR < bestDR) {
        bestDR = dR;
        subIdx = j;
      }
    }
    const bool hasSub = (subIdx != -1);

    // GSF-derived features
    const math::PtEtaPhiMLorentzVector trk1(gPt[m], gEta[m], gPhi[m], kEleMass);
    float gsfPtRatio = kSentinel, gsfDeltaR = kSentinel, gsfRelPtRatio = gPt[m] / scRawEn;
    if (hasSub) {
      const math::PtEtaPhiMLorentzVector trk2(gPt[subIdx], gEta[subIdx], gPhi[subIdx], kEleMass);
      gsfPtRatio = gPt[subIdx] / gPt[m];
      gsfDeltaR = reco::deltaR(gEta[m], gPhi[m], gEta[subIdx], gPhi[subIdx]);
      gsfRelPtRatio = (trk1 + trk2).pt() / scRawEn;
    }

    // --- publish the track-level quantities the downstream analysis rebuilds the candidate from ---
    oMPt[i] = gPt[m];  oMEta[i] = gEta[m];  oMPhi[i] = gPhi[m];
    oMD0[i] = gD0[m];  oMDz[i] = gDz[m];    oMCharge[i] = gCharge[m];
    oMMiss[i] = gMiss[m];  oMLost[i] = gLost[m];
    oMPix[i] = gPix[m];    oMLayers[i] = gLayers[m];
    oHasAdd[i] = hasSub ? 1 : 0;
    oRelPtRatio[i] = gsfRelPtRatio;
    if (hasSub) {
      const math::PtEtaPhiMLorentzVector t1(gPt[m], gEta[m], gPhi[m], kEleMass);
      const math::PtEtaPhiMLorentzVector t2(gPt[subIdx], gEta[subIdx], gPhi[subIdx], kEleMass);
      oAPt[i] = gPt[subIdx];  oAEta[i] = gEta[subIdx];  oAPhi[i] = gPhi[subIdx];
      oAD0[i] = gD0[subIdx];  oADz[i] = gDz[subIdx];    oACharge[i] = gCharge[subIdx];
      oAMiss[i] = gMiss[subIdx];  oALost[i] = gLost[subIdx];
      oAPix[i] = gPix[subIdx];    oALayers[i] = gLayers[subIdx];
      oPtRatio[i] = gsfPtRatio;
      oDeltaR[i] = gsfDeltaR;
      oPtSum[i] = gPt[m] + gPt[subIdx];
      oDiTrkPt[i] = (t1 + t2).pt();
      oDiTrkMass[i] = (t1 + t2).M();  // <- the merged-electron mass used downstream
    }

    // standard electron features (exactly as ggNtuplizer computes them)
    float elePtError = ele.hasUserFloat("ecalTrkEnergyErrPostCorr")
                           ? ele.userFloat("ecalTrkEnergyErrPostCorr") * ele.pt() / ele.p()
                           : ele.correctedEcalEnergyError() * ele.pt() / ele.p();
    float eleEoverPInv = (ele.ecalEnergy() == 0.f || !edm::isFinite(ele.ecalEnergy()))
                             ? 1e30f
                             : (1.0f - ele.eSuperClusterOverP()) / ele.ecalEnergy();
    const auto& pfIso = ele.pfIsolationVariables();

    // feature vector, in the exact training order (M1 drops gsfPtRatio & gsfDeltaR)
    std::vector<float> feats;
    feats.reserve(22);
    feats.push_back(static_cast<float>(rho));
    feats.push_back(scEta);
    feats.push_back(scRawEn);
    feats.push_back(ele.deltaEtaSuperClusterTrackAtVtx());
    feats.push_back(ele.deltaPhiSuperClusterTrackAtVtx());
    feats.push_back(elePtError);
    feats.push_back(ele.hcalOverEcal());
    feats.push_back(ele.eSuperClusterOverP());
    feats.push_back(ele.eEleClusterOverPout());
    feats.push_back(eleEoverPInv);
    feats.push_back(ele.superCluster()->etaWidth());
    feats.push_back(ele.superCluster()->phiWidth());
    feats.push_back(ele.full5x5_sigmaIetaIeta());
    feats.push_back(ele.full5x5_sigmaIphiIphi());
    feats.push_back(ele.full5x5_r9());
    feats.push_back(ele.fbrem());
    feats.push_back(pfIso.sumChargedHadronPt);
    feats.push_back(pfIso.sumPhotonEt);
    feats.push_back(pfIso.sumNeutralHadronEt);
    if (hasSub) {  // Merged-2Gsf order
      feats.push_back(gsfPtRatio);
      feats.push_back(gsfDeltaR);
    }
    feats.push_back(gsfRelPtRatio);

    const HDalitzMergedEstimatorBase* est = hasSub ? (isEB ? m2EB_.get() : m2EE_.get())
                                                   : (isEB ? m1EB_.get() : m1EE_.get());
    const double wp = hasSub ? (isEB ? m2EBWP_ : m2EEWP_) : (isEB ? m1EBWP_ : m1EEWP_);
    outCat[i] = hasSub ? (isEB ? 2 : 3) : (isEB ? 0 : 1);

    const std::vector<float> scores = est->predict(feats);
    if (!scores.empty()) {
      outScore[i] = scores[0];  // merged-signal class probability
      const int argmax = static_cast<int>(std::max_element(scores.begin(), scores.end()) - scores.begin());
      outWP[i] = (argmax == 0 && scores[0] > static_cast<float>(wp)) ? 1 : 0;
    }
  }

  writeValueMap(iEvent, eleHandle, outScore, "hdalitzMergedIDScore");
  writeValueMap(iEvent, eleHandle, outNGsf, "hdalitzMergedNGsf");
  writeValueMap(iEvent, eleHandle, outCat, "hdalitzMergedCategory");
  writeValueMap(iEvent, eleHandle, outWP, "hdalitzMergedWPTight");

  writeValueMap(iEvent, eleHandle, oMPt, "hdalitzMainGsfPt");
  writeValueMap(iEvent, eleHandle, oMEta, "hdalitzMainGsfEta");
  writeValueMap(iEvent, eleHandle, oMPhi, "hdalitzMainGsfPhi");
  writeValueMap(iEvent, eleHandle, oMD0, "hdalitzMainGsfD0");
  writeValueMap(iEvent, eleHandle, oMDz, "hdalitzMainGsfDz");
  writeValueMap(iEvent, eleHandle, oAPt, "hdalitzAddGsfPt");
  writeValueMap(iEvent, eleHandle, oAEta, "hdalitzAddGsfEta");
  writeValueMap(iEvent, eleHandle, oAPhi, "hdalitzAddGsfPhi");
  writeValueMap(iEvent, eleHandle, oAD0, "hdalitzAddGsfD0");
  writeValueMap(iEvent, eleHandle, oADz, "hdalitzAddGsfDz");
  writeValueMap(iEvent, eleHandle, oPtRatio, "hdalitzGsfPtRatio");
  writeValueMap(iEvent, eleHandle, oDeltaR, "hdalitzGsfDeltaR");
  writeValueMap(iEvent, eleHandle, oRelPtRatio, "hdalitzGsfRelPtRatio");
  writeValueMap(iEvent, eleHandle, oPtSum, "hdalitzGsfPtSum");
  writeValueMap(iEvent, eleHandle, oDiTrkPt, "hdalitzDiTrkPt");
  writeValueMap(iEvent, eleHandle, oDiTrkMass, "hdalitzDiTrkMass");

  writeValueMap(iEvent, eleHandle, oMCharge, "hdalitzMainGsfCharge");
  writeValueMap(iEvent, eleHandle, oMMiss, "hdalitzMainGsfMissHits");
  writeValueMap(iEvent, eleHandle, oMLost, "hdalitzMainGsfLostHits");
  writeValueMap(iEvent, eleHandle, oMPix, "hdalitzMainGsfPixelHits");
  writeValueMap(iEvent, eleHandle, oMLayers, "hdalitzMainGsfLayers");
  writeValueMap(iEvent, eleHandle, oACharge, "hdalitzAddGsfCharge");
  writeValueMap(iEvent, eleHandle, oAMiss, "hdalitzAddGsfMissHits");
  writeValueMap(iEvent, eleHandle, oALost, "hdalitzAddGsfLostHits");
  writeValueMap(iEvent, eleHandle, oAPix, "hdalitzAddGsfPixelHits");
  writeValueMap(iEvent, eleHandle, oALayers, "hdalitzAddGsfLayers");
  writeValueMap(iEvent, eleHandle, oHasAdd, "hdalitzHasAddGsf");
}

template <typename T>
void HDalitzMergedIDProducer::writeValueMap(edm::Event& iEvent,
                                            const edm::Handle<edm::View<pat::Electron>>& handle,
                                            const std::vector<T>& values,
                                            const std::string& label) {
  auto out = std::make_unique<edm::ValueMap<T>>();
  typename edm::ValueMap<T>::Filler filler(*out);
  filler.insert(handle, values.begin(), values.end());
  filler.fill();
  iEvent.put(std::move(out), label);
}

DEFINE_FWK_MODULE(HDalitzMergedIDProducer);
