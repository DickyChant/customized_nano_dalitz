#include "PhysicsTools/SelectorUtils/interface/CutApplicatorWithEventContentBase.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "RecoEgamma/EgammaTools/interface/EleEnergyRetriever.h"

#include "RecoEgamma/ElectronIdentification/interface/EBEECutValues.h"

// a hack of RecoEgamma/ElectronIdentification/plugins/cuts/GsfEleValueMapIsoRhoCut.cc

class GsfEleModifiedEmHadD1IsoRhoCut : public CutApplicatorWithEventContentBase {
public:
  GsfEleModifiedEmHadD1IsoRhoCut(const edm::ParameterSet& c);

  result_type operator()(const reco::GsfElectronPtr&) const final;

  void setConsumes(edm::ConsumesCollector&) final;
  void getEventContent(const edm::EventBase&) final;

  double value(const reco::CandidatePtr& cand) const final;

  CandidateType candidateType() const final {
    return ELECTRON;
  }

private:
  float rhoConstant_;
  EBEECutValues slopeTerm_;
  EBEECutValues slopeStart_;
  EBEECutValues constTerm_;
  EleEnergyRetriever energyRetriever_;

  edm::Handle<double> rhoHandle_;
  edm::Handle<edm::ValueMap<float>> valueHandle_;
  edm::Handle<edm::ValueMap<reco::GsfTrackRef>> addGsfTrkHandle_;
  edm::Handle<edm::ValueMap<pat::PackedCandidateRef>> addPackedCandHandle_;
};

DEFINE_EDM_PLUGIN(CutApplicatorFactory,
                  GsfEleModifiedEmHadD1IsoRhoCut,
                  "GsfEleModifiedEmHadD1IsoRhoCut");

GsfEleModifiedEmHadD1IsoRhoCut::GsfEleModifiedEmHadD1IsoRhoCut(const edm::ParameterSet& params) :
  CutApplicatorWithEventContentBase(params),
  rhoConstant_(params.getParameter<double>("rhoConstant")),
  slopeTerm_(params,"slopeTerm"),
  slopeStart_(params,"slopeStart"),
  constTerm_(params,"constTerm"),
  energyRetriever_(params.getParameter<std::string>("energyType"))
{
  edm::InputTag rhoTag = params.getParameter<edm::InputTag>("rho");
  contentTags_.emplace("rho",rhoTag);
  contentTags_.emplace("value",params.getParameter<edm::InputTag>("value"));
  contentTags_.emplace("addGsfTrk",params.getParameter<edm::InputTag>("addGsfTrk"));
  contentTags_.emplace("addPackedCand",params.getParameter<edm::InputTag>("addPackedCand"));
}

void GsfEleModifiedEmHadD1IsoRhoCut::setConsumes(edm::ConsumesCollector& cc) {
  auto rho = cc.consumes<double>(contentTags_["rho"]);
  contentTokens_.emplace("rho",rho);
  contentTokens_.emplace("value",cc.consumes<edm::ValueMap<float>>(contentTags_["value"]));
  contentTokens_.emplace("addGsfTrk",cc.consumes<edm::ValueMap<reco::GsfTrackRef>>(contentTags_["addGsfTrk"]));
  contentTokens_.emplace("addPackedCand",cc.consumes<edm::ValueMap<pat::PackedCandidateRef>>(contentTags_["addPackedCand"]));
}

void GsfEleModifiedEmHadD1IsoRhoCut::getEventContent(const edm::EventBase& ev) {
  ev.getByLabel(contentTags_["rho"],rhoHandle_);
  ev.getByLabel(contentTags_["value"],valueHandle_);
  ev.getByLabel(contentTags_["addGsfTrk"],addGsfTrkHandle_);
  ev.getByLabel(contentTags_["addPackedCand"],addPackedCandHandle_);
}

CutApplicatorBase::result_type GsfEleModifiedEmHadD1IsoRhoCut::operator() (const reco::GsfElectronPtr& cand) const {
  const double rho = (*rhoHandle_);
  const double isolEmHadDepth1 = value(cand);

  const float sinTheta = cand->p()!=0. ? cand->pt()/cand->p() : 0.;
  const float et = energyRetriever_(*cand)*sinTheta;

  const float cutValue = et > slopeStart_(cand)  ? slopeTerm_(cand)*(et-slopeStart_(cand)) + constTerm_(cand) : constTerm_(cand);
  return isolEmHadDepth1 < cutValue + rhoConstant_*rho;
}

double GsfEleModifiedEmHadD1IsoRhoCut::value(const reco::CandidatePtr& cand) const {
  reco::GsfElectronPtr ele(cand);
  const bool has2ndTrk = (*addGsfTrkHandle_)[ele]!=ele->gsfTrack() || (*addPackedCandHandle_)[ele].isNonnull();
  const double ecalIso = has2ndTrk ? (*valueHandle_)[ele] : ele->dr03EcalRecHitSumEt();

  return ecalIso + ele->dr03HcalDepth1TowerSumEt();
}
