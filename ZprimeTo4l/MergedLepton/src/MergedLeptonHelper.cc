#include "ZprimeTo4l/MergedLepton/interface/MergedLeptonHelper.h"

#include "Geometry/CaloGeometry/interface/CaloGeometry.h"
#include "Geometry/CaloGeometry/interface/CaloCellGeometry.h"
#include "Geometry/Records/interface/CaloGeometryRecord.h"

#include "Geometry/CaloTopology/interface/CaloTopology.h"
#include "Geometry/CaloEventSetup/interface/CaloTopologyRecord.h"
#include "RecoEcal/EgammaCoreTools/interface/EcalClusterTools.h"
#include "DataFormats/EcalDetId/interface/EcalSubdetector.h"
#include "DataFormats/EcalRecHit/interface/EcalRecHit.h"

#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "RecoVertex/KalmanVertexFit/interface/KalmanVertexFitter.h"

bool MergedLeptonHelperFct::isNotMerged(const pat::ElectronRef& aEle,
                                        const edm::Handle<edm::View<pat::Electron>>& eleHandle,
                                        const reco::GsfTrackRef& addGsfTrk) {
  // additional GSF track must not be an electron
  bool notMerged = false;

  // additional GSF track is not selected
  if (aEle->gsfTrack()==addGsfTrk)
    return notMerged;

  // GSF track must be ambiguous
  for (unsigned int jdx = 0; jdx < eleHandle->size(); ++jdx) {
    const auto& secEle = eleHandle->refAt(jdx);
    const auto& secGsfTrk = secEle->gsfTrack();

    if (aEle==secEle.castTo<pat::ElectronRef>())
      continue;

    if ( addGsfTrk==secGsfTrk ) {
      notMerged = true;
      break;
    }
  }

  return notMerged;
}

MergedLeptonHelper::MergedLeptonHelper()
: pFS_(nullptr) {
  dielstr_ = TString("weight/F:Gen1stPt:Gen2ndPt:GenDR:")
  + "passReco1/I:passReco2:"
  + "passHEEP1:passHEEP2:passHEEPIso1:passHEEPIso2:passHEEPnoIso1:passHEEPnoIso2:"
  + "passModHeep1:passModHeep2:passModHeepIso1:passModHeepIso2:passModHEEPnoIso1:passModHEEPnoIso2:"
  + "nGSFtrk:nKFtrk:category:passME:"
  + "mergedEleMvaScore/F";

  elstr_ = TString("weight/F:pt:eta:phi:en:et:charge/I:")
  + "enSC/F:etSC:etaSC:phiSC:etaSeed:phiSeed:etaSCWidth:phiSCWidth:"
  + "full5x5_sigmaIetaIeta:full5x5_sigmaIphiIphi:"
  + "full5x5_E1x5:full5x5_E2x5:full5x5_E5x5:full5x5_hOverE:full5x5_r9:"
  + "dEtaIn:dPhiIn:dPhiSeed:dEtaEle:dPhiEle:dEtaSeed:"
  + "EseedOverP:EOverP:"
  + "ecalEn:ecalErr:trkErr:combErr:PFcombErr:"
  + "dr03TkSumPtHEEP:dr03EcalRecHitSumEt:dr03HcalDepth1TowerSumEt:"
  + "modTrkIso/F:modEcalIso:"
  + "passEMHad1Iso/I:passHEEP:passHEEPnoIso:"
  + "passModEMHad1Iso:passModHeep:passModHEEPnoIso:passME:"
  + "mergedEleMvaScore/F:"
  + "lostHits/I:nValidHits:nValidPixelHits:GsfHits:"
  + "chi2/F:d0:d0Err:dxyErr:vz:dzErr:dxy:dz:"
  + "Gsfpt/F:Gsfeta:Gsfphi:GsfPtErr:"
  + "expectedMissingInnerHits/I:"
  + "convDist/F:convDcot:convRadius:"
  + "passConversionVeto/I:nbrem:"
  + "fbrem/F:fbremSC:"
  + "full5x5_e2x5Left:full5x5_e2x5Right:full5x5_e2x5Top:full5x5_e2x5Bottom:"
  + "full5x5_eLeft:full5x5_eRight:full5x5_eTop:full5x5_eBottom:"
  + "full5x5_eMax:full5x5_e2nd:"
  + "clus2ndMoment_sMaj:clus2ndMoment_sMin:clus2ndMoment_alpha:"
  + "dEtaSeedMiniAOD:dPhiInMiniAOD:sigIeIeMiniAOD:"
  + "union5x5dEtaIn:union5x5dPhiIn:"
  + "union5x5Energy:union5x5covIeIe:union5x5covIeIp:union5x5covIpIp:"
  + "union5x5covMaj:union5x5covMin:"
  + "alphaCalo:"
  + "GenPt:GenE:"
  + "Gen2ndPt:GenDR:"
  + "nGSFtrk/I:nKFtrk:"
  + "u5x5numGood:u5x5numPoorReco:u5x5numOutOfTime:u5x5numFaultyHardware:"
  + "u5x5numNoisy:u5x5numPoorCalib:u5x5numSaturated:u5x5numLeadingEdgeRecovered:"
  + "u5x5NeighboursRecovered:u5x5numTowerRecovered:u5x5numDead:u5x5numKilled:"
  + "u5x5numTPSaturated:u5x5numL1SpikeFlag:u5x5numWeird:u5x5numDiWeird:"
  + "u5x5numHasSwitchToGain6:u5x5numHasSwitchToGain1:u5x5numUnknown:"
  + "u5x5numTPSaturatedAndTowerRecovered";

  addtrkstr_ = TString("weight/F:pt:eta:phi:")
  + "lostHits/I:nValidHits:nValidPixelHits:charge:chargeProduct:isPackedCand:"
  + "chi2/F:d0:d0Err:dxyErr:vz:dzErr:dxy:dz:ptErr:"
  + "deltaEtaSeedClusterAtVtx:deltaPhiSuperClusterAtVtx:"
  + "dPerpIn:normalizedDParaIn:alphaTrack:"
  + "vtxLxy:vtxProb:vtxChi2:vtxNdof:dR";
}

void MergedLeptonHelper::initDielTree(const std::string& name,
                                      const std::string& prefix,
                                      const std::string& postfix) {
  dielvalues_[prefix+"_"+postfix] = DielStruct();
  tree_[prefix+"_"+postfix+"Tree"] = (*pFS_)->make<TTree>(TString(prefix)+"_"+postfix+"Tree",TString(postfix)+"Tree");
  tree_[prefix+"_"+postfix+"Tree"]->Branch(TString(name),&(dielvalues_[prefix+"_"+postfix]),dielstr_);
}

void MergedLeptonHelper::initElectronTree(const std::string& name,
                                          const std::string& prefix,
                                          const std::string& postfix) {
  elvalues_[prefix+"_"+postfix] = ElectronStruct();
  tree_[prefix+"_"+postfix+"Tree"] = (*pFS_)->make<TTree>(TString(prefix)+"_"+postfix+"Tree",TString(postfix)+"Tree");
  tree_[prefix+"_"+postfix+"Tree"]->Branch(TString(name),&(elvalues_[prefix+"_"+postfix]),elstr_);
}

void MergedLeptonHelper::initAddTrkTree(const std::string& name,
                                        const std::string& prefix,
                                        const std::string& postfix) {
  trkvalues_[prefix+"_"+postfix] = AddTrkStruct();
  tree_[prefix+"_"+postfix+"Tree"] = (*pFS_)->make<TTree>(TString(prefix)+"_"+postfix+"Tree",TString(postfix)+"Tree");
  tree_[prefix+"_"+postfix+"Tree"]->Branch(TString(name),&(trkvalues_[prefix+"_"+postfix]),addtrkstr_);
}

void MergedLeptonHelper::fillDielectrons(const pat::ElectronRef& e1,
                                         const pat::ElectronRef& e2,
                                         const reco::GenParticleRef& p1,
                                         const reco::GenParticleRef& p2,
                                         const int category,
                                         const std::string& prefix,
                                         const int nGSFtrk,
                                         const int nKFtrk) {
  dielvalues_[prefix+"_diel"].weight = mcweight_;
  dielvalues_[prefix+"_diel"].Gen1stPt = p1->pt();
  dielvalues_[prefix+"_diel"].Gen2ndPt = p2->pt();
  dielvalues_[prefix+"_diel"].GenDR = reco::deltaR(p1->eta(),p1->phi(),p2->eta(),p2->phi());

  int32_t maskIso = 0x00000E7F; // = 1110 0111 1111 - 7th for trk iso, 8th for EM+HadD1 iso
  int32_t maskNoIso = 0x00000180; // = 0001 1000 0000 - 7th for trk iso, 8th for EM+HadD1 iso

  dielvalues_[prefix+"_diel"].nGSFtrk = nGSFtrk;
  dielvalues_[prefix+"_diel"].nKFtrk = nKFtrk;
  dielvalues_[prefix+"_diel"].category = category;

  dielvalues_[prefix+"_diel"].passReco1 = static_cast<int>(e1.isNonnull());

  dielvalues_[prefix+"_diel"].passHEEP1 = -1;
  dielvalues_[prefix+"_diel"].passHEEPIso1 = -1;
  dielvalues_[prefix+"_diel"].passHEEPnoIso1 = -1;
  dielvalues_[prefix+"_diel"].passModHeep1 = -1;
  dielvalues_[prefix+"_diel"].passModHeepIso1 = -1;
  dielvalues_[prefix+"_diel"].passModHEEPnoIso1 = -1;
  dielvalues_[prefix+"_diel"].passME = -1;
  dielvalues_[prefix+"_diel"].mergedEleMvaScore = -1.;

  if (e1.isNonnull()) {
    dielvalues_[prefix+"_diel"].passHEEP1 = e1->electronID("heepElectronID-HEEPV70");
    int32_t bitmapHEEP1 = e1->userInt("heepElectronID-HEEPV70");
    dielvalues_[prefix+"_diel"].passHEEPIso1 = static_cast<int>( (bitmapHEEP1 | maskIso)==0x00000FFF );
    dielvalues_[prefix+"_diel"].passHEEPnoIso1 = static_cast<int>( (bitmapHEEP1 | maskNoIso)==0x00000FFF );

    dielvalues_[prefix+"_diel"].passModHeep1 = e1->electronID("modifiedHeepElectronID");
    int32_t bitmapModHEEP1 = e1->userInt("modifiedHeepElectronID");
    dielvalues_[prefix+"_diel"].passModHeepIso1 = static_cast<int>( (bitmapModHEEP1 | maskIso)==0x00000FFF );
    dielvalues_[prefix+"_diel"].passModHEEPnoIso1 = static_cast<int>( (bitmapModHEEP1 | maskNoIso)==0x00000FFF );

    dielvalues_[prefix+"_diel"].passME = static_cast<int>( e1->electronID("mvaMergedElectron") );
    dielvalues_[prefix+"_diel"].mergedEleMvaScore = e1->userFloat("mvaMergedElectronValues");
  }

  dielvalues_[prefix+"_diel"].passReco2 = static_cast<int>(e2.isNonnull());

  dielvalues_[prefix+"_diel"].passHEEP2 = -1;
  dielvalues_[prefix+"_diel"].passHEEPIso2 = -1;
  dielvalues_[prefix+"_diel"].passHEEPnoIso2 = -1;
  dielvalues_[prefix+"_diel"].passModHeep2 = -1;
  dielvalues_[prefix+"_diel"].passModHeepIso2 = -1;
  dielvalues_[prefix+"_diel"].passModHEEPnoIso2 = -1;

  if (e2.isNonnull()) {
    dielvalues_[prefix+"_diel"].passHEEP2 = e2->electronID("heepElectronID-HEEPV70");
    int32_t bitmapHEEP2 = e2->userInt("heepElectronID-HEEPV70");
    dielvalues_[prefix+"_diel"].passHEEPIso2 = static_cast<int>( (bitmapHEEP2 | maskIso)==0x00000FFF );
    dielvalues_[prefix+"_diel"].passHEEPnoIso2 = static_cast<int>( (bitmapHEEP2 | maskNoIso)==0x00000FFF );

    dielvalues_[prefix+"_diel"].passModHeep2 = e2->electronID("modifiedHeepElectronID");
    int32_t bitmapModHEEP2 = e2->userInt("modifiedHeepElectronID");
    dielvalues_[prefix+"_diel"].passModHeepIso2 = static_cast<int>( (bitmapModHEEP2 | maskIso)==0x00000FFF );
    dielvalues_[prefix+"_diel"].passModHEEPnoIso2 = static_cast<int>( (bitmapModHEEP2 | maskNoIso)==0x00000FFF );
  }

  tree_[prefix+"_dielTree"]->Fill();
}

void MergedLeptonHelper::fillElectrons(const pat::ElectronRef& el,
                                       const float& trkIso,
                                       const float& ecalIso,
                                       const ModifiedDEtaInSeed::variables& variablesDEtaIn,
                                       const ModifiedShowerShape::variables& variables,
                                       const EcalRecHitCollection* ecalRecHits,
                                       const edm::EventSetup& iSetup,
                                       const std::string& prefix,
                                       const float genPt,
                                       const float genE,
                                       const int nGSFtrk, const int nKFtrk,
                                       const float Gen2ndPt, const float GenDR) {
  auto square = [](const double& val) { return val*val; };
  double rad = std::sqrt(square(el->superCluster()->x()) + square(el->superCluster()->y()) + square(el->superCluster()->z()));
  double radTrans = std::sqrt(square(el->superCluster()->x()) + square(el->superCluster()->y()));

  elvalues_[prefix+"_el"].weight = mcweight_;

  elvalues_[prefix+"_el"].pt = el->pt();
  elvalues_[prefix+"_el"].eta = el->eta();
  elvalues_[prefix+"_el"].phi = el->phi();
  elvalues_[prefix+"_el"].en = el->energy();
  elvalues_[prefix+"_el"].et = el->et();
  elvalues_[prefix+"_el"].charge = el->charge();

  elvalues_[prefix+"_el"].enSC = el->superCluster()->energy();
  elvalues_[prefix+"_el"].etSC = (el->superCluster()->energy())*(radTrans/rad);
  elvalues_[prefix+"_el"].etaSC = el->superCluster()->eta();
  elvalues_[prefix+"_el"].phiSC = el->superCluster()->phi();
  elvalues_[prefix+"_el"].etaSeed = el->superCluster()->seed()->eta();
  elvalues_[prefix+"_el"].phiSeed = el->superCluster()->seed()->phi();
  elvalues_[prefix+"_el"].etaSCWidth = el->superCluster()->etaWidth();
  elvalues_[prefix+"_el"].phiSCWidth = el->superCluster()->phiWidth();

  elvalues_[prefix+"_el"].full5x5_sigmaIetaIeta = el->full5x5_sigmaIetaIeta();
  elvalues_[prefix+"_el"].full5x5_sigmaIphiIphi = el->full5x5_sigmaIphiIphi();
  elvalues_[prefix+"_el"].full5x5_E1x5 = el->full5x5_e1x5();
  elvalues_[prefix+"_el"].full5x5_E2x5 = el->full5x5_e2x5Max();
  elvalues_[prefix+"_el"].full5x5_E5x5 = el->full5x5_e5x5();
  elvalues_[prefix+"_el"].full5x5_hOverE = el->full5x5_hcalOverEcal();
  elvalues_[prefix+"_el"].full5x5_r9 = el->full5x5_r9();

  elvalues_[prefix+"_el"].dEtaIn = el->deltaEtaSuperClusterTrackAtVtx();
  elvalues_[prefix+"_el"].dPhiIn = el->deltaPhiSuperClusterTrackAtVtx();
  elvalues_[prefix+"_el"].dPhiSeed = el->deltaPhiSeedClusterTrackAtCalo();
  elvalues_[prefix+"_el"].dEtaEle = el->deltaEtaEleClusterTrackAtCalo();
  elvalues_[prefix+"_el"].dPhiEle = el->deltaPhiEleClusterTrackAtCalo();
  elvalues_[prefix+"_el"].dEtaSeed = el->deltaEtaSeedClusterTrackAtVtx();
  elvalues_[prefix+"_el"].EseedOverP = el->eSeedClusterOverP();
  elvalues_[prefix+"_el"].EOverP = el->eSuperClusterOverP();

  elvalues_[prefix+"_el"].ecalEn = el->ecalEnergy();
  elvalues_[prefix+"_el"].ecalErr = el->ecalEnergyError();
  elvalues_[prefix+"_el"].trkErr = el->trackMomentumError();
  elvalues_[prefix+"_el"].combErr = el->p4Error(reco::GsfElectron::P4_COMBINATION);
  elvalues_[prefix+"_el"].PFcombErr = el->p4Error(reco::GsfElectron::P4_PFLOW_COMBINATION);

  elvalues_[prefix+"_el"].dr03TkSumPtHEEP = el->dr03TkSumPtHEEP();
  elvalues_[prefix+"_el"].dr03EcalRecHitSumEt = el->dr03EcalRecHitSumEt();
  elvalues_[prefix+"_el"].dr03HcalDepth1TowerSumEt = el->dr03HcalDepth1TowerSumEt();
  elvalues_[prefix+"_el"].modTrkIso = trkIso;
  elvalues_[prefix+"_el"].modEcalIso = ecalIso;

  int32_t bitmapHEEP = el->userInt("heepElectronID-HEEPV70");
  int32_t maskIso = 0x00000E7F; // = 1110 0111 1111 - 7th for trk iso, 8th for EM+HadD1 iso
  int32_t maskEMHad1Iso = 0x00000EFF; // = 1110 1111 1111 - 7th for trk iso, 8th for EM+HadD1 iso
  int32_t maskNoIso = 0x00000180; // = 0001 1000 0000 - 7th for trk iso, 8th for EM+HadD1 iso
  elvalues_[prefix+"_el"].passEMHad1Iso = static_cast<int>( (bitmapHEEP | maskEMHad1Iso)==0x00000FFF );
  elvalues_[prefix+"_el"].passHEEPnoIso = static_cast<int>( (bitmapHEEP | maskNoIso)==0x00000FFF );
  elvalues_[prefix+"_el"].passHEEP = static_cast<int>( el->electronID("heepElectronID-HEEPV70") );

  int32_t bitmapModHEEP = el->userInt("modifiedHeepElectronID");
  elvalues_[prefix+"_el"].passModEMHad1Iso = static_cast<int>( (bitmapModHEEP | maskEMHad1Iso)==0x00000FFF );
  elvalues_[prefix+"_el"].passModHEEPnoIso = static_cast<int>( (bitmapModHEEP | maskNoIso)==0x00000FFF );
  elvalues_[prefix+"_el"].passModHeep = static_cast<int>( el->electronID("modifiedHeepElectronID") );
  elvalues_[prefix+"_el"].passME = static_cast<int>( el->electronID("mvaMergedElectron") );
  elvalues_[prefix+"_el"].mergedEleMvaScore = el->userFloat("mvaMergedElectronValues");

  const auto GSFtrack = el->gsfTrack();
  elvalues_[prefix+"_el"].lostHits = GSFtrack->hitPattern().numberOfLostHits(reco::HitPattern::MISSING_INNER_HITS);
  elvalues_[prefix+"_el"].nValidHits = GSFtrack->hitPattern().numberOfValidHits();
  elvalues_[prefix+"_el"].nValidPixelHits = GSFtrack->hitPattern().numberOfValidPixelHits();
  elvalues_[prefix+"_el"].chi2 = GSFtrack->normalizedChi2();
  elvalues_[prefix+"_el"].GsfHits = GSFtrack->hitPattern().trackerLayersWithMeasurement();

  elvalues_[prefix+"_el"].d0 = GSFtrack->d0();
  elvalues_[prefix+"_el"].d0Err = GSFtrack->d0Error();
  elvalues_[prefix+"_el"].dxyErr = GSFtrack->dxyError();
  elvalues_[prefix+"_el"].vz = GSFtrack->vz();
  elvalues_[prefix+"_el"].dzErr = GSFtrack->dzError();

  elvalues_[prefix+"_el"].dxy = GSFtrack->dxy(pPV_->position());
  elvalues_[prefix+"_el"].dz = GSFtrack->dz(pPV_->position());

  elvalues_[prefix+"_el"].Gsfpt = GSFtrack->pt();
  elvalues_[prefix+"_el"].Gsfeta = GSFtrack->eta();
  elvalues_[prefix+"_el"].Gsfphi = GSFtrack->phi();
  elvalues_[prefix+"_el"].GsfPtErr = GSFtrack->ptError();

  elvalues_[prefix+"_el"].expectedMissingInnerHits = el->gsfTrack()->hitPattern().numberOfAllHits(reco::HitPattern::MISSING_INNER_HITS); // 94X

  elvalues_[prefix+"_el"].passConversionVeto = el->passConversionVeto();
  elvalues_[prefix+"_el"].convDist = el->convDist();
  elvalues_[prefix+"_el"].convDcot = el->convDcot();
  elvalues_[prefix+"_el"].convRadius = el->convRadius();

  elvalues_[prefix+"_el"].fbrem = el->fbrem();
  elvalues_[prefix+"_el"].nbrem = el->numberOfBrems();
  elvalues_[prefix+"_el"].fbremSC = el->superClusterFbrem();

  elvalues_[prefix+"_el"].full5x5_eMax = el->full5x5_showerShape().eMax;
  elvalues_[prefix+"_el"].full5x5_e2nd = el->full5x5_showerShape().e2nd;

  elvalues_[prefix+"_el"].full5x5_e2x5Left = el->full5x5_e2x5Left();
  elvalues_[prefix+"_el"].full5x5_e2x5Right = el->full5x5_e2x5Right();
  elvalues_[prefix+"_el"].full5x5_e2x5Top = el->full5x5_e2x5Top();
  elvalues_[prefix+"_el"].full5x5_e2x5Bottom = el->full5x5_e2x5Bottom();
  elvalues_[prefix+"_el"].full5x5_eLeft = el->full5x5_eLeft();
  elvalues_[prefix+"_el"].full5x5_eRight = el->full5x5_eRight();
  elvalues_[prefix+"_el"].full5x5_eTop = el->full5x5_eTop();
  elvalues_[prefix+"_el"].full5x5_eBottom = el->full5x5_eBottom();

  std::vector<std::pair<const EcalRecHit*,float>> recHitsAndFractions;

  for (auto& xtal : el->superCluster()->hitsAndFractions()) {
    EcalRecHitCollection::const_iterator aRecHit = ecalRecHits->find(xtal.first);

    if ( aRecHit!=ecalRecHits->end() )
      recHitsAndFractions.push_back( std::make_pair(&(*aRecHit),xtal.second) );
  }

  const reco::CaloClusterPtr seedClus = el->superCluster()->seed();
  auto cluster2ndMoments = noZS::EcalClusterTools::cluster2ndMoments(recHitsAndFractions,1.0);
  elvalues_[prefix+"_el"].clus2ndMoment_sMaj = cluster2ndMoments.sMaj;
  elvalues_[prefix+"_el"].clus2ndMoment_sMin = cluster2ndMoments.sMin;
  elvalues_[prefix+"_el"].clus2ndMoment_alpha = cluster2ndMoments.alpha;

  elvalues_[prefix+"_el"].dEtaSeedMiniAOD = std::numeric_limits<float>::max();
  elvalues_[prefix+"_el"].dPhiInMiniAOD = std::numeric_limits<float>::max();

  auto dEtaInSeedCalc = ModifiedDEtaInSeed(posCalcLog_);
  auto scAtVtx = EleRelPointPair(math::XYZPoint(),math::XYZPoint(),pBS_->position());
  auto seedAtCalo = EleRelPointPair(math::XYZPoint(),math::XYZPoint(),pBS_->position());

  if ( dEtaInSeedCalc.extrapolate(*el,*(el->gsfTrack()),pBS_->position(),iSetup,scAtVtx,seedAtCalo) ) {
    elvalues_[prefix+"_el"].dEtaSeedMiniAOD = scAtVtx.dEta() - el->superCluster()->eta() + el->superCluster()->seed()->eta();
    elvalues_[prefix+"_el"].dPhiInMiniAOD = scAtVtx.dPhi();
  }

  elvalues_[prefix+"_el"].union5x5dEtaIn = variables.dEtaInUnion5x5;
  elvalues_[prefix+"_el"].union5x5dPhiIn = variables.dPhiInUnion5x5;
  elvalues_[prefix+"_el"].union5x5Energy = variables.union5x5Energy;
  elvalues_[prefix+"_el"].union5x5covIeIe = variables.covEE;
  elvalues_[prefix+"_el"].union5x5covIeIp = variables.covEP;
  elvalues_[prefix+"_el"].union5x5covIpIp = variables.covPP;
  elvalues_[prefix+"_el"].alphaCalo = variables.alpha;

  double covEE = variables.covEE;
  double covEP = variables.covEP;
  double covPP = variables.covPP;
  double covMaj = ((covEE + covPP) + std::sqrt((covEE - covPP)*(covEE - covPP) + 4.*covEP*covEP)) / 2.;
  double covMin = ((covEE + covPP) - std::sqrt((covEE - covPP)*(covEE - covPP) + 4.*covEP*covEP)) / 2.;
  elvalues_[prefix+"_el"].union5x5covMaj = covMaj;
  elvalues_[prefix+"_el"].union5x5covMin = covMin;

  // Get Calo Topology
  edm::ESHandle<CaloTopology> caloTopoHandle;
  iSetup.get<CaloTopologyRecord>().get(caloTopoHandle);
  const CaloTopology* caloTopo = caloTopoHandle.product();

  auto matrix5x5of1stGSF = noZS::EcalClusterTools::matrixDetId(caloTopo, el->superCluster()->seed()->seed(), 2 );
  std::vector<DetId> unionMatrix5x5(matrix5x5of1stGSF);
  std::vector<std::pair<DetId,float>> hitFracUnion5x5;

  for (const auto& adetId : unionMatrix5x5)
    hitFracUnion5x5.push_back(std::make_pair(adetId,1.));

  auto showerShapeCalc = ModifiedShowerShape(posCalcLog_);

  double sumE = noZS::EcalClusterTools::e5x5(*(el->superCluster()->seed()),ecalRecHits,caloTopo);
  auto sigmas = showerShapeCalc.calcSigmas(*el,hitFracUnion5x5,ecalRecHits,sumE);
  double sigEE = std::get<0>(sigmas);
  elvalues_[prefix+"_el"].sigIeIeMiniAOD = 0.01745*std::sqrt(sigEE);

  // signal MC only
  elvalues_[prefix+"_el"].GenPt = genPt;
  elvalues_[prefix+"_el"].GenE = genE;
  elvalues_[prefix+"_el"].Gen2ndPt = Gen2ndPt;
  elvalues_[prefix+"_el"].GenDR = GenDR;
  elvalues_[prefix+"_el"].nGSFtrk = nGSFtrk;
  elvalues_[prefix+"_el"].nKFtrk = nKFtrk;

  // temporary recHit status check
  auto setRecHitFlags = [&,this] (int aFlag) {
    elvalues_[prefix+"_el"].u5x5numGood = aFlag;
    elvalues_[prefix+"_el"].u5x5numPoorReco = aFlag;
    elvalues_[prefix+"_el"].u5x5numOutOfTime = aFlag;
    elvalues_[prefix+"_el"].u5x5numFaultyHardware = aFlag;
    elvalues_[prefix+"_el"].u5x5numNoisy = aFlag;
    elvalues_[prefix+"_el"].u5x5numPoorCalib = aFlag;
    elvalues_[prefix+"_el"].u5x5numSaturated = aFlag;
    elvalues_[prefix+"_el"].u5x5numLeadingEdgeRecovered = aFlag;
    elvalues_[prefix+"_el"].u5x5NeighboursRecovered = aFlag;
    elvalues_[prefix+"_el"].u5x5numTowerRecovered = aFlag;
    elvalues_[prefix+"_el"].u5x5numDead = aFlag;
    elvalues_[prefix+"_el"].u5x5numKilled = aFlag;
    elvalues_[prefix+"_el"].u5x5numTPSaturated = aFlag;
    elvalues_[prefix+"_el"].u5x5numL1SpikeFlag = aFlag;
    elvalues_[prefix+"_el"].u5x5numWeird = aFlag;
    elvalues_[prefix+"_el"].u5x5numDiWeird = aFlag;
    elvalues_[prefix+"_el"].u5x5numHasSwitchToGain6 = aFlag;
    elvalues_[prefix+"_el"].u5x5numHasSwitchToGain1 = aFlag;
    elvalues_[prefix+"_el"].u5x5numUnknown = aFlag;
    elvalues_[prefix+"_el"].u5x5numTPSaturatedAndTowerRecovered = aFlag;
  };

  setRecHitFlags(-1);

  // Get Calo Geometry
  edm::ESHandle<CaloGeometry> caloGeoHandle;
  iSetup.get<CaloGeometryRecord>().get(caloGeoHandle);
  const CaloGeometry* caloGeom = caloGeoHandle.product();

  auto searchClosestXtal = [&ecalRecHits,&caloGeom] (const float eta, const float phi) -> DetId {
    float dR2 = std::numeric_limits<float>::max();
    DetId candId = DetId(0);

    for (auto& xtal : *ecalRecHits) {
      const auto& xtalGeo = caloGeom->getGeometry(xtal.detid());
      float candDR2 = reco::deltaR2(eta,phi,xtalGeo->etaPos(),xtalGeo->phiPos());

      if (candDR2 < dR2) {
        dR2 = candDR2;
        candId = xtal.detid();
      }
    }

    return candId;
  };

  const float eta1stGSF = -( el->deltaEtaSeedClusterTrackAtVtx() - el->superCluster()->seed()->eta() );
  const float phi1stGSF = reco::reduceRange( -( el->deltaPhiSuperClusterTrackAtVtx() - el->superCluster()->phi() ) );

  const DetId xtal1st = searchClosestXtal(eta1stGSF,phi1stGSF);

  if ( xtal1st!=DetId(0) ) {
    unionMatrix5x5 = noZS::EcalClusterTools::matrixDetId(caloTopo, xtal1st, 2 );

    if ( variablesDEtaIn.dEtaInSeed2nd!=std::numeric_limits<float>::max() &&
         variablesDEtaIn.dPhiInSC2nd!=std::numeric_limits<float>::max() ) {
      const float eta2ndGSF = -( variablesDEtaIn.dEtaInSeed2nd - el->superCluster()->seed()->eta() );
      const float phi2ndGSF = reco::reduceRange( -( variablesDEtaIn.dPhiInSC2nd - el->superCluster()->phi() ) );

      const DetId xtal2nd = searchClosestXtal(eta2ndGSF,phi2ndGSF);

      if ( xtal2nd!=DetId(0) ) {
        auto matrix5x5of2ndGSF = noZS::EcalClusterTools::matrixDetId(caloTopo, xtal2nd, 2 );

        for (auto& adetId : matrix5x5of2ndGSF) {
          if ( std::find(unionMatrix5x5.begin(),unionMatrix5x5.end(),adetId)==unionMatrix5x5.end() )
            unionMatrix5x5.push_back(adetId);
        }
      } // if xtal2nd!=DetId(0)
    } // if 2nd track

    setRecHitFlags(0);

    for (const auto& recHit : *ecalRecHits) {
      if ( std::find(unionMatrix5x5.begin(),unionMatrix5x5.end(),recHit.detid())!=unionMatrix5x5.end() ) {
        if (recHit.checkFlag(EcalRecHit::Flags::kGood))
          elvalues_[prefix+"_el"].u5x5numGood += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kPoorReco))
          elvalues_[prefix+"_el"].u5x5numPoorReco += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kOutOfTime))
          elvalues_[prefix+"_el"].u5x5numOutOfTime += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kFaultyHardware))
          elvalues_[prefix+"_el"].u5x5numFaultyHardware += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kNoisy))
          elvalues_[prefix+"_el"].u5x5numNoisy += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kPoorCalib))
          elvalues_[prefix+"_el"].u5x5numPoorCalib += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kSaturated))
          elvalues_[prefix+"_el"].u5x5numSaturated += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kLeadingEdgeRecovered))
          elvalues_[prefix+"_el"].u5x5numLeadingEdgeRecovered += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kNeighboursRecovered))
          elvalues_[prefix+"_el"].u5x5NeighboursRecovered += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kTowerRecovered))
          elvalues_[prefix+"_el"].u5x5numTowerRecovered += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kDead))
          elvalues_[prefix+"_el"].u5x5numDead += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kKilled))
          elvalues_[prefix+"_el"].u5x5numKilled += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kTPSaturated))
          elvalues_[prefix+"_el"].u5x5numTPSaturated += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kL1SpikeFlag))
          elvalues_[prefix+"_el"].u5x5numL1SpikeFlag += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kWeird))
          elvalues_[prefix+"_el"].u5x5numWeird += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kDiWeird))
          elvalues_[prefix+"_el"].u5x5numDiWeird += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kHasSwitchToGain6))
          elvalues_[prefix+"_el"].u5x5numHasSwitchToGain6 += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kHasSwitchToGain1))
          elvalues_[prefix+"_el"].u5x5numHasSwitchToGain1 += 1;
        if (recHit.checkFlag(EcalRecHit::Flags::kUnknown))
          elvalues_[prefix+"_el"].u5x5numUnknown += 1;
        if ( recHit.checkFlag(EcalRecHit::Flags::kTPSaturated) && recHit.checkFlag(EcalRecHit::Flags::kTowerRecovered) )
          elvalues_[prefix+"_el"].u5x5numTPSaturatedAndTowerRecovered += 1;
      } // if unionMatrix5x5
    } // for ecalRecHits
  } // if xtal1st!=DetId(0)

  tree_[prefix+"_elTree"]->Fill();
}

void MergedLeptonHelper::fillAddTracks(const pat::ElectronRef& el,
                                       const reco::Track* addTrk,
                                       const ModifiedDEtaInSeed::variables& variables,
                                       const EcalRecHitCollection* ecalRecHits,
                                       const edm::EventSetup& iSetup,
                                       const std::string& prefix,
                                       const bool isPackedCand) {
  trkvalues_[prefix+"_addTrk"].weight = mcweight_;

  trkvalues_[prefix+"_addTrk"].pt = addTrk->pt();
  trkvalues_[prefix+"_addTrk"].eta = addTrk->eta();
  trkvalues_[prefix+"_addTrk"].phi = addTrk->phi();
  trkvalues_[prefix+"_addTrk"].lostHits = addTrk->hitPattern().numberOfLostHits(reco::HitPattern::MISSING_INNER_HITS);
  trkvalues_[prefix+"_addTrk"].nValidHits = addTrk->hitPattern().numberOfValidHits();
  trkvalues_[prefix+"_addTrk"].nValidPixelHits = addTrk->hitPattern().numberOfValidPixelHits();
  trkvalues_[prefix+"_addTrk"].chi2 = addTrk->normalizedChi2();
  trkvalues_[prefix+"_addTrk"].d0 = addTrk->d0();
  trkvalues_[prefix+"_addTrk"].d0Err = addTrk->d0Error();
  trkvalues_[prefix+"_addTrk"].dxyErr = addTrk->dxyError();
  trkvalues_[prefix+"_addTrk"].vz = addTrk->vz();
  trkvalues_[prefix+"_addTrk"].dzErr = addTrk->dzError();

  trkvalues_[prefix+"_addTrk"].dxy = addTrk->dxy(pPV_->position());
  trkvalues_[prefix+"_addTrk"].dz = addTrk->dz(pPV_->position());
  trkvalues_[prefix+"_addTrk"].ptErr = addTrk->ptError();

  trkvalues_[prefix+"_addTrk"].deltaEtaSeedClusterAtVtx = variables.dEtaInSeed2nd;
  trkvalues_[prefix+"_addTrk"].deltaPhiSuperClusterAtVtx = variables.dPhiInSC2nd;
  trkvalues_[prefix+"_addTrk"].dPerpIn = variables.dPerpIn;
  trkvalues_[prefix+"_addTrk"].alphaTrack = variables.alphaTrack;
  trkvalues_[prefix+"_addTrk"].normalizedDParaIn = variables.normalizedDParaIn;

  trkvalues_[prefix+"_addTrk"].charge = addTrk->charge();
  trkvalues_[prefix+"_addTrk"].chargeProduct = el->gsfTrack()->charge()*addTrk->charge();
  trkvalues_[prefix+"_addTrk"].isPackedCand = static_cast<int>(isPackedCand);
  trkvalues_[prefix+"_addTrk"].dR = reco::deltaR(el->gsfTrack()->eta(),el->gsfTrack()->phi(),
                                                 addTrk->eta(),addTrk->phi());

  // vtx fit info
  edm::ESHandle<TransientTrackBuilder> TTbuilder;
  auto fitter = KalmanVertexFitter();
  iSetup.get<TransientTrackRecord>().get("TransientTrackBuilder",TTbuilder);
  auto firstEle = TTbuilder->build(el->gsfTrack());

  std::vector<reco::TransientTrack> trackPair;
  trackPair.push_back(firstEle);
  trackPair.push_back(TTbuilder->build(addTrk));

  TransientVertex aVtx = fitter.vertex(trackPair);

  trkvalues_[prefix+"_addTrk"].vtxLxy = -1.;
  trkvalues_[prefix+"_addTrk"].vtxProb = -1.;
  trkvalues_[prefix+"_addTrk"].vtxChi2 = -1.;
  trkvalues_[prefix+"_addTrk"].vtxNdof = -1.;

  if (aVtx.isValid()) {
    trkvalues_[prefix+"_addTrk"].vtxLxy = aVtx.vertexState().position().perp();
    trkvalues_[prefix+"_addTrk"].vtxProb = TMath::Prob(aVtx.totalChiSquared(),static_cast<int>(std::rint(aVtx.degreesOfFreedom())));
    trkvalues_[prefix+"_addTrk"].vtxChi2 = aVtx.totalChiSquared();
    trkvalues_[prefix+"_addTrk"].vtxNdof = aVtx.degreesOfFreedom();
  }

  tree_[prefix+"_addTrkTree"]->Fill();
}
