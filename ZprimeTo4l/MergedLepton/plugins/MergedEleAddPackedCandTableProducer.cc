// Publishes the PF-based "additional leg" of a merged electron as electron ValueMaps.
//
// Why this exists: a merged electron's second leg is EITHER a second GSF track OR a packed PF
// candidate. In practice ~85% of electrons have NO second GSF track (measured on UL18 signal),
// so for the large majority the packed candidate is the only handle on the second leg -- and
// it carries lostInnerHits(), which is the conversion discriminator that actually works in
// MiniAOD. (A ref-based per-GSF-track conversion veto is impossible here: MiniAOD conversions
// are built from general tracks whose Refs are dropped, so ConversionTools ref-matching never
// fires, and geometric leg matching is only ~12% pure.)
//
// ModifiedHEEPIDValueMapProducer already finds this candidate ("eleAddPackedCand"); this only
// flattens it into branchable per-electron values.

#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "DataFormats/Common/interface/ValueMap.h"
#include "DataFormats/Common/interface/View.h"
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"

#include <memory>
#include <vector>

class MergedEleAddPackedCandTableProducer : public edm::stream::EDProducer<> {
public:
  explicit MergedEleAddPackedCandTableProducer(const edm::ParameterSet&);
  ~MergedEleAddPackedCandTableProducer() override = default;

private:
  void produce(edm::Event&, const edm::EventSetup&) override;
  template <typename T>
  void put(edm::Event&, const edm::Handle<edm::View<pat::Electron>>&,
           const std::vector<T>&, const std::string&);

  const edm::EDGetTokenT<edm::View<pat::Electron>> eleToken_;
  const edm::EDGetTokenT<edm::ValueMap<pat::PackedCandidateRef>> candToken_;

  static constexpr float kSentinel = -999.f;
};

MergedEleAddPackedCandTableProducer::MergedEleAddPackedCandTableProducer(const edm::ParameterSet& cfg)
    : eleToken_(consumes<edm::View<pat::Electron>>(cfg.getParameter<edm::InputTag>("srcEle"))),
      candToken_(consumes<edm::ValueMap<pat::PackedCandidateRef>>(
          cfg.getParameter<edm::InputTag>("addPackedCandMap"))) {
  for (const char* l : {"Pt", "Eta", "Phi", "Dxy", "Dz"})
    produces<edm::ValueMap<float>>(std::string("addPackedCand") + l);
  for (const char* l : {"Charge", "LostInnerHits", "PixelHits", "NHits", "HighPurity", "Exists"})
    produces<edm::ValueMap<int>>(std::string("addPackedCand") + l);
}

void MergedEleAddPackedCandTableProducer::produce(edm::Event& iEvent, const edm::EventSetup&) {
  auto eleHandle = iEvent.getHandle(eleToken_);
  const auto& cands = iEvent.get(candToken_);
  const size_t n = eleHandle->size();

  std::vector<float> pt(n, kSentinel), eta(n, kSentinel), phi(n, kSentinel),
      dxy(n, kSentinel), dz(n, kSentinel);
  std::vector<int> q(n, 0), lih(n, -99), pix(n, -1), nh(n, -1), hp(n, -1), ex(n, 0);

  for (size_t i = 0; i < n; ++i) {
    const auto& ref = cands[eleHandle->refAt(i)];
    if (ref.isNull())
      continue;
    ex[i] = 1;
    pt[i] = ref->pt();
    eta[i] = ref->eta();
    phi[i] = ref->phi();
    dxy[i] = ref->dxy();
    dz[i] = ref->dz();
    q[i] = ref->charge();
    // -1 validHitInFirstPixelBarrelLayer (most conversion-unlike), 0 none, 1 one, 2 more
    lih[i] = static_cast<int>(ref->lostInnerHits());
    pix[i] = ref->numberOfPixelHits();
    nh[i] = ref->numberOfHits();
    hp[i] = ref->trackHighPurity() ? 1 : 0;
  }

  put(iEvent, eleHandle, pt, "addPackedCandPt");
  put(iEvent, eleHandle, eta, "addPackedCandEta");
  put(iEvent, eleHandle, phi, "addPackedCandPhi");
  put(iEvent, eleHandle, dxy, "addPackedCandDxy");
  put(iEvent, eleHandle, dz, "addPackedCandDz");
  put(iEvent, eleHandle, q, "addPackedCandCharge");
  put(iEvent, eleHandle, lih, "addPackedCandLostInnerHits");
  put(iEvent, eleHandle, pix, "addPackedCandPixelHits");
  put(iEvent, eleHandle, nh, "addPackedCandNHits");
  put(iEvent, eleHandle, hp, "addPackedCandHighPurity");
  put(iEvent, eleHandle, ex, "addPackedCandExists");
}

template <typename T>
void MergedEleAddPackedCandTableProducer::put(edm::Event& iEvent,
                                              const edm::Handle<edm::View<pat::Electron>>& h,
                                              const std::vector<T>& v, const std::string& label) {
  auto out = std::make_unique<edm::ValueMap<T>>();
  typename edm::ValueMap<T>::Filler filler(*out);
  filler.insert(h, v.begin(), v.end());
  filler.fill();
  iEvent.put(std::move(out), label);
}

DEFINE_FWK_MODULE(MergedEleAddPackedCandTableProducer);
