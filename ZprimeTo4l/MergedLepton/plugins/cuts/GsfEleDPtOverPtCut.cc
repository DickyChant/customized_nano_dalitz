#include "PhysicsTools/SelectorUtils/interface/CutApplicatorWithEventContentBase.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/Common/interface/ValueMap.h"

class GsfEleDPtOverPtCut : public CutApplicatorWithEventContentBase {
public:
  GsfEleDPtOverPtCut(const edm::ParameterSet& c);

  result_type operator() (const reco::GsfElectronPtr&) const final;

  void setConsumes(edm::ConsumesCollector&) final;
  void getEventContent(const edm::EventBase&) final;

  double value(const reco::CandidatePtr& cand) const final;

  CandidateType candidateType() const final { return ELECTRON; }

private:
  const double cutValue_;
  edm::Handle<edm::ValueMap<reco::GsfTrackRef>> addGsfTrkHandle_;
  edm::Handle<edm::ValueMap<pat::PackedCandidateRef>> addPackedCandHandle_;
};

DEFINE_EDM_PLUGIN(CutApplicatorFactory,
                  GsfEleDPtOverPtCut,
                  "GsfEleDPtOverPtCut");

GsfEleDPtOverPtCut::GsfEleDPtOverPtCut(const edm::ParameterSet& c) :
  CutApplicatorWithEventContentBase(c),
  cutValue_(c.getParameter<double>("dPtOverPtCutValue"))
{
  contentTags_.emplace("addGsfTrk",c.getParameter<edm::InputTag>("addGsfTrk"));
  contentTags_.emplace("addPackedCand",c.getParameter<edm::InputTag>("addPackedCand"));
}

void GsfEleDPtOverPtCut::setConsumes(edm::ConsumesCollector& cc) {
  contentTokens_.emplace("addGsfTrk",cc.consumes<edm::ValueMap<reco::GsfTrackRef>>(contentTags_["addGsfTrk"]));
  contentTokens_.emplace("addPackedCand",cc.consumes<edm::ValueMap<pat::PackedCandidateRef>>(contentTags_["addPackedCand"]));
}

void GsfEleDPtOverPtCut::getEventContent(const edm::EventBase& ev) {
  ev.getByLabel(contentTags_["addGsfTrk"],addGsfTrkHandle_);
  ev.getByLabel(contentTags_["addPackedCand"],addPackedCandHandle_);
}

CutApplicatorBase::result_type GsfEleDPtOverPtCut::operator() (const reco::GsfElectronPtr& cand) const {
  const bool has2ndTrk = (*addGsfTrkHandle_)[cand]!=cand->gsfTrack() || (*addPackedCandHandle_)[cand].isNonnull();

  if (has2ndTrk)
    return true;

  return value(cand) < cutValue_;
}

double GsfEleDPtOverPtCut::value(const reco::CandidatePtr& cand) const {
  reco::GsfElectronPtr ele(cand);

  return ele->gsfTrack()->ptError()/ele->gsfTrack()->pt();
}
