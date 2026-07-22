#include <iostream>

#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/Math/interface/deltaPhi.h"

#include "ZprimeTo4l/MergedLepton/interface/MergedMvaEstimator.h"

class MergedLeptonIDProducer : public edm::stream::EDProducer<> {
public:
  explicit MergedLeptonIDProducer(const edm::ParameterSet&);
  ~MergedLeptonIDProducer() override {}

private:
  enum MvaCategory {
    Nulltype = -1,
    HasTrk,  // has 2nd track & 20 GeV < Et
    NoTrkEt2 // no 2nd track
  };

  void produce(edm::Event&, const edm::EventSetup&) override;

  template<typename T>
  void writeValueMap( edm::Event& iEvent,
                      const edm::Handle<edm::View<pat::Electron>>& handle,
                      const std::vector<T>& values,
                      const std::string& label );

  const edm::EDGetTokenT<edm::View<pat::Electron>> eleToken_;
  const edm::EDGetTokenT<edm::ValueMap<reco::GsfTrackRef>> addGsfTrkToken_;
  const edm::EDGetTokenT<edm::ValueMap<pat::PackedCandidateRef>> addPackedCandToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> dPerpInToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> dEtaInSeed2ndToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> dPhiInSC2ndToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> alphaTrackToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> alphaCaloToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> normDParaInToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> union5x5covIeIeToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> union5x5covIeIpToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> union5x5covIpIpToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> union5x5dEtaInToken_;
  const edm::EDGetTokenT<edm::ValueMap<float>> union5x5dPhiInToken_;

  const edm::FileInPath xgbPathHasTrkEB_;
  const edm::FileInPath xgbPathNoneEt2EB_;
  const edm::FileInPath meanstdPathHasTrkEB_;
  const edm::FileInPath meanstdPathNoneEt2EB_;

  const std::unique_ptr<MergedMvaEstimator> xgbEstimatorHasTrkEB_;
  const std::unique_ptr<MergedMvaEstimator> xgbEstimatorNoneEt2EB_;
};

MergedLeptonIDProducer::MergedLeptonIDProducer(const edm::ParameterSet& iConfig)
: eleToken_(consumes<edm::View<pat::Electron>>(iConfig.getParameter<edm::InputTag>("srcEle"))),
  addGsfTrkToken_(consumes<edm::ValueMap<reco::GsfTrackRef>>(iConfig.getParameter<edm::InputTag>("addGsfTrkMap"))),
  addPackedCandToken_(consumes<edm::ValueMap<pat::PackedCandidateRef>>(iConfig.getParameter<edm::InputTag>("addPackedCandMap"))),
  dPerpInToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("dPerpIn"))),
  dEtaInSeed2ndToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("dEtaInSeed2nd"))),
  dPhiInSC2ndToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("dPhiInSC2nd"))),
  alphaTrackToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("alphaTrack"))),
  alphaCaloToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("alphaCalo"))),
  normDParaInToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("normalizedDParaIn"))),
  union5x5covIeIeToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("union5x5covIeIe"))),
  union5x5covIeIpToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("union5x5covIeIp"))),
  union5x5covIpIpToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("union5x5covIpIp"))),
  union5x5dEtaInToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("union5x5dEtaIn"))),
  union5x5dPhiInToken_(consumes<edm::ValueMap<float>>(iConfig.getParameter<edm::InputTag>("union5x5dPhiIn"))),
  xgbPathHasTrkEB_(iConfig.getParameter<edm::FileInPath>("xgbPathHasTrkEB")),
  xgbPathNoneEt2EB_(iConfig.getParameter<edm::FileInPath>("xgbPathNoneEt2EB")),
  meanstdPathHasTrkEB_(iConfig.getParameter<edm::FileInPath>("meanstdPathHasTrkEB")),
  meanstdPathNoneEt2EB_(iConfig.getParameter<edm::FileInPath>("meanstdPathNoneEt2EB")),
  xgbEstimatorHasTrkEB_(std::make_unique<MergedMvaEstimator>(xgbPathHasTrkEB_,meanstdPathHasTrkEB_)),
  xgbEstimatorNoneEt2EB_(std::make_unique<MergedMvaEstimator>(xgbPathNoneEt2EB_,meanstdPathNoneEt2EB_)) {
  produces<edm::ValueMap<float>>("mvaMergedElectronValues");
  produces<edm::ValueMap<int>>("mvaMergedElectronCategories");
}

template<typename T>
void MergedLeptonIDProducer::writeValueMap( edm::Event& iEvent,
                                            const edm::Handle<edm::View<pat::Electron>>& handle,
                                            const std::vector<T>& values,
                                            const std::string& label ) {
  auto valMap = std::make_unique<edm::ValueMap<T>>();
  typename edm::ValueMap<T>::Filler filler(*valMap);
  filler.insert(handle, values.begin(), values.end());
  filler.fill();
  iEvent.put(std::move(valMap),label);
}

void MergedLeptonIDProducer::produce(edm::Event& iEvent, const edm::EventSetup& iSetup) {
  edm::Handle<edm::View<pat::Electron>> eleHandle;
  iEvent.getByToken(eleToken_, eleHandle);

  edm::Handle<edm::ValueMap<reco::GsfTrackRef>> addGsfTrkHandle;
  iEvent.getByToken(addGsfTrkToken_, addGsfTrkHandle);

  edm::Handle<edm::ValueMap<pat::PackedCandidateRef>> addPackedCandHandle;
  iEvent.getByToken(addPackedCandToken_, addPackedCandHandle);

  edm::Handle<edm::ValueMap<float>> dPerpInHandle;
  iEvent.getByToken(dPerpInToken_, dPerpInHandle);

  edm::Handle<edm::ValueMap<float>> dEtaInSeed2ndHandle;
  iEvent.getByToken(dEtaInSeed2ndToken_, dEtaInSeed2ndHandle);

  edm::Handle<edm::ValueMap<float>> dPhiInSC2ndHandle;
  iEvent.getByToken(dPhiInSC2ndToken_, dPhiInSC2ndHandle);

  edm::Handle<edm::ValueMap<float>> alphaTrackHandle;
  iEvent.getByToken(alphaTrackToken_, alphaTrackHandle);

  edm::Handle<edm::ValueMap<float>> alphaCaloHandle;
  iEvent.getByToken(alphaCaloToken_, alphaCaloHandle);

  edm::Handle<edm::ValueMap<float>> normDParaInHandle;
  iEvent.getByToken(normDParaInToken_, normDParaInHandle);

  edm::Handle<edm::ValueMap<float>> union5x5covIeIeHandle;
  iEvent.getByToken(union5x5covIeIeToken_, union5x5covIeIeHandle);

  edm::Handle<edm::ValueMap<float>> union5x5covIeIpHandle;
  iEvent.getByToken(union5x5covIeIpToken_, union5x5covIeIpHandle);

  edm::Handle<edm::ValueMap<float>> union5x5covIpIpHandle;
  iEvent.getByToken(union5x5covIpIpToken_, union5x5covIpIpHandle);

  edm::Handle<edm::ValueMap<float>> union5x5dEtaInHandle;
  iEvent.getByToken(union5x5dEtaInToken_, union5x5dEtaInHandle);

  edm::Handle<edm::ValueMap<float>> union5x5dPhiInHandle;
  iEvent.getByToken(union5x5dPhiInToken_, union5x5dPhiInHandle);

  unsigned int nEle = eleHandle->size();

  std::vector<float> mvas_mergedElectron;
  mvas_mergedElectron.reserve(nEle);
  std::vector<int> trkType_mergedElectron;
  trkType_mergedElectron.reserve(nEle);

  for (unsigned int idx = 0; idx < eleHandle->size(); ++idx) {
    const auto& aEle = eleHandle->refAt(idx);
    const auto& orgGsfTrk = aEle->gsfTrack();

    const auto& addGsfTrk = (*addGsfTrkHandle)[aEle];
    const auto& addPackedCand = (*addPackedCandHandle)[aEle];

    const auto dEtaVariables = ModifiedDEtaInSeed::variables((*dPerpInHandle)[aEle],
                                                             (*dEtaInSeed2ndHandle)[aEle],
                                                             (*dPhiInSC2ndHandle)[aEle],
                                                             (*alphaTrackHandle)[aEle],
                                                             (*normDParaInHandle)[aEle]);
    const auto ssVariables = ModifiedShowerShape::variables((*union5x5covIeIeHandle)[aEle],
                                                             (*union5x5covIeIpHandle)[aEle],
                                                             (*union5x5covIpIpHandle)[aEle],
                                                             (*alphaCaloHandle)[aEle],
                                                             (*union5x5dEtaInHandle)[aEle],
                                                             (*union5x5dPhiInHandle)[aEle],
                                                             0.);

    // default category is bkgEt2EB (no 2nd GSF)
    MvaCategory aTrkType_mergedElectron = MvaCategory::NoTrkEt2;
    double amvascore_mergedElectron = -1.;

    if ( addGsfTrk==orgGsfTrk && addPackedCand.isNull() ) {
      // no additional GSF track
      // need to apply an additional offline Et cut afterwards
      if ( std::abs(aEle->superCluster()->eta()) < 1.5 ) {
        const auto castEle = aEle.castTo<pat::ElectronRef>();
        amvascore_mergedElectron = xgbEstimatorNoneEt2EB_->computeMva(castEle);
      }
    } else {
      // has additional GSF track
      aTrkType_mergedElectron = MvaCategory::HasTrk;

      if ( std::abs(aEle->superCluster()->eta()) < 1.5 ) {
        const auto castEle = aEle.castTo<pat::ElectronRef>();
        amvascore_mergedElectron = xgbEstimatorHasTrkEB_->computeMva(castEle,dEtaVariables,ssVariables);
      } // isEB
    } // end isSameGsfTrack

    mvas_mergedElectron.emplace_back(amvascore_mergedElectron);
    trkType_mergedElectron.emplace_back( static_cast<int>(aTrkType_mergedElectron) );
  } // electron loop

  writeValueMap(iEvent,eleHandle,mvas_mergedElectron,"mvaMergedElectronValues");
  writeValueMap(iEvent,eleHandle,trkType_mergedElectron,"mvaMergedElectronCategories");

  return;
}

DEFINE_FWK_MODULE(MergedLeptonIDProducer);
