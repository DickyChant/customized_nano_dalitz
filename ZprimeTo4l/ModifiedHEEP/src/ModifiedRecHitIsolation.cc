//*****************************************************************************
// File:      ModifiedRecHitIsolation.cc
// ----------------------------------------------------------------------------
// OrigAuth:  Matthias Mozer, hacked by Sam Harper (ie the ugly stuff is mine)
// Institute: IIHE-VUB, RAL
//=============================================================================
//*****************************************************************************
//C++ includes
#include <vector>
#include <functional>

//ROOT includes
#include <Math/VectorUtil.h>

//CMSSW includes
#include "ZprimeTo4l/ModifiedHEEP/interface/ModifiedRecHitIsolation.h"
#include "DataFormats/DetId/interface/DetId.h"
#include "DataFormats/EcalDetId/interface/EcalSubdetector.h"
#include "DataFormats/GeometryVector/interface/GlobalPoint.h"
#include "DataFormats/GeometryVector/interface/GlobalVector.h"
#include "DataFormats/EgammaReco/interface/BasicCluster.h"
#include "DataFormats/EgammaReco/interface/BasicClusterFwd.h"
#include "DataFormats/CaloRecHit/interface/CaloCluster.h"
#include "DataFormats/CaloRecHit/interface/CaloClusterFwd.h"
#include "DataFormats/EgammaReco/interface/SuperCluster.h"
#include "DataFormats/EgammaReco/interface/SuperClusterFwd.h"
#include "DataFormats/RecoCandidate/interface/RecoCandidate.h"
#include "DataFormats/Math/interface/deltaPhi.h"

#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/GsfTrackReco/interface/GsfTrack.h"
#include "DataFormats/GsfTrackReco/interface/GsfTrackFwd.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectronFwd.h"

using namespace std;

ModifiedRecHitIsolation::ModifiedRecHitIsolation(double extRadius,
                                                 double intRadius,
                                                 double etaSlice,
                                                 double etLow,
                                                 double eLow,
                                                 edm::ESHandle<CaloGeometry> theCaloGeom,
                                                 const EcalRecHitCollection& caloHits,
                                                 const EcalSeverityLevelAlgo* sl,
                                                 DetId::Detector detector, // not used anymore, kept for compatibility
                                                 std::vector<int> recHitFlags,
                                                 std::vector<int> recHitSeverity):
  extRadius_(extRadius),
  intRadius_(intRadius),
  etaSlice_(etaSlice),
  etLow_(etLow),
  eLow_(eLow),
  theCaloGeom_(theCaloGeom),
  caloHits_(caloHits),
  sevLevel_(sl),
  useNumCrystals_(false),
  vetoClustered_(false),
  ecalBarHits_(nullptr),
  severitiesexcl_(0),
  flags_(0)
{
  //set up the geometry and selector
  const CaloGeometry* caloGeom = theCaloGeom_.product();
  subdet_[0] = caloGeom->getSubdetectorGeometry(DetId::Ecal,EcalBarrel);
  subdet_[1] = caloGeom->getSubdetectorGeometry(DetId::Ecal,EcalEndcap);

  doFlagChecks(recHitFlags);
  doSeverityChecks(&caloHits,recHitSeverity);
}

ModifiedRecHitIsolation::~ModifiedRecHitIsolation() {}

float ModifiedRecHitIsolation::getSum_(const reco::GsfElectron* emObject, const reco::TrackBase& addTrk,
                                       const float dEtaInSeed2nd, const float dPhiInSC2nd, bool returnEt) const {
  float energySum = 0.;

  if (!caloHits_.empty()) {
    // Take the GSF track & SC position
    const auto& sc = emObject->superCluster();
    const math::XYZPoint& theCaloPosition = sc->position();
    const GlobalPoint pclu( theCaloPosition.x (), theCaloPosition.y (), theCaloPosition.z () );
    const float etaclus = pclu.eta();
    const float eta1stGSF = -( emObject->deltaEtaSeedClusterTrackAtVtx() - emObject->superCluster()->seed()->eta() );
    const float phi1stGSF = reco::reduceRange( -( emObject->deltaPhiSuperClusterTrackAtVtx() - emObject->superCluster()->phi() ) );
    const float eta2ndGSF = (std::abs(dEtaInSeed2nd) > extRadius_)
                            ? eta1stGSF : -( dEtaInSeed2nd - emObject->superCluster()->seed()->eta() );
    const float phi2ndGSF = (std::abs(dPhiInSC2nd) > extRadius_)
                            ? phi1stGSF : reco::reduceRange( -( dPhiInSC2nd - emObject->superCluster()->phi() ) );
    float r2 = intRadius_*intRadius_;

    std::vector< std::pair<DetId, float> >::const_iterator rhIt;

    for (int subdetnr = 0; subdetnr <= 1 ; subdetnr++) { // look in barrel and endcap
      if( nullptr == subdet_[subdetnr] )
        continue;

      CaloSubdetectorGeometry::DetIdSet chosen = subdet_[subdetnr]->getCells(pclu,extRadius_); // select cells around cluster
      EcalRecHitCollection::const_iterator j = caloHits_.end();

      for (CaloSubdetectorGeometry::DetIdSet::const_iterator i = chosen.begin(); i != chosen.end(); ++i) { //loop selected cells
        j = caloHits_.find(*i); // find selected cell among rechits

        if (j != caloHits_.end()) { // add rechit only if available
          auto cell = theCaloGeom_->getGeometry(*i);
          float eta = cell->etaPos();
          float phi = cell->phiPos();
          float etaDiff = eta - eta1stGSF;
          float phiDiff = reco::deltaPhi(phi,phi1stGSF);
          float energy = j->energy();
          float etaDiff2nd = eta - eta2ndGSF;
          float phiDiff2nd = reco::deltaPhi(phi,phi2ndGSF);

          if (useNumCrystals_) {
            if (std::abs(etaclus) < 1.479) { // Barrel num crystals, crystal width = 0.0174
              if (std::abs(etaDiff) < 0.0174*etaSlice_)
                continue;
              if ((etaDiff*etaDiff + phiDiff*phiDiff) < 0.00030276*r2)
                continue;
              if (std::abs(etaDiff2nd) < 0.0174*etaSlice_)
                continue;
              if ((etaDiff2nd*etaDiff2nd + phiDiff2nd*phiDiff2nd) < 0.00030276*r2)
                continue;
            } else { // Endcap num crystals, crystal width = 0.00864*fabs(sinh(eta))
              if (std::abs(etaDiff) < 0.00864*std::abs(std::sinh(eta))*etaSlice_)
                continue;
              if ((etaDiff*etaDiff + phiDiff*phiDiff) < (0.000037325*(std::cosh(2*eta)-1)*r2))
                continue;
              if (std::abs(etaDiff2nd) < 0.00864*std::abs(std::sinh(eta))*etaSlice_)
                continue;
              if ((etaDiff2nd*etaDiff2nd + phiDiff2nd*phiDiff2nd) < (0.000037325*(std::cosh(2*eta)-1)*r2))
                continue;
            }
          } else {
            if (std::abs(etaDiff) < etaSlice_)
              continue; // jurassic strip cut
            if (etaDiff*etaDiff + phiDiff*phiDiff < r2)
              continue; // jurassic exclusion cone cut
            if (std::abs(etaDiff2nd) < etaSlice_)
              continue; // jurassic strip cut
            if (etaDiff2nd*etaDiff2nd + phiDiff2nd*phiDiff2nd < r2)
              continue; // jurassic exclusion cone cut
          }

          // Check if RecHit is in SC
          if (vetoClustered_) {
            // Loop over basic clusters:
            bool isClustered = false;
            for (reco::CaloCluster_iterator bcIt = sc->clustersBegin(); bcIt != sc->clustersEnd(); ++bcIt) {
              for (rhIt = (*bcIt)->hitsAndFractions().begin(); rhIt != (*bcIt)->hitsAndFractions().end(); ++rhIt) {
                if (rhIt->first == *i)
                  isClustered = true;
                if (isClustered)
                  break;
              }

              if (isClustered)
                break;
            } // end loop over basic clusters

            if (isClustered)
              continue;
          } // end if removeClustered

          int severityFlag = ecalBarHits_ == nullptr ? -1 : sevLevel_->severityLevel(j->detid(), *ecalBarHits_);
          std::vector<int>::const_iterator sit = std::find(severitiesexcl_.begin(),severitiesexcl_.end(),severityFlag);

          if ( sit != severitiesexcl_.end() )
            continue;

          if (!j->checkFlag(EcalRecHit::kGood)) {
            if (j->checkFlags(flags_))
              continue;
          }

          float et = energy*std::sqrt(cell->getPosition().perp2()/cell->getPosition().mag2());

          if ( et > etLow_ && energy > eLow_) { //Changed energy --> fabs(energy) - now changed back to energy
            if (returnEt)
              energySum += et;
            else
              energySum += energy;
          }
        } // End if not end of list
      } // End loop over rechits
    } // End loop over barrel/endcap
  } // End if caloHits_

  return energySum;
}
