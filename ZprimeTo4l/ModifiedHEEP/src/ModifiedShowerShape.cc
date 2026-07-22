#include "ZprimeTo4l/ModifiedHEEP/interface/ModifiedShowerShape.h"

#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/Math/interface/deltaPhi.h"

#include "Geometry/CaloGeometry/interface/CaloGeometry.h"
#include "Geometry/CaloGeometry/interface/CaloCellGeometry.h"
#include "Geometry/Records/interface/CaloGeometryRecord.h"

#include "Geometry/CaloTopology/interface/CaloTopology.h"
#include "Geometry/CaloEventSetup/interface/CaloTopologyRecord.h"
#include "RecoEcal/EgammaCoreTools/interface/EcalClusterTools.h"
#include "DataFormats/EcalDetId/interface/EcalSubdetector.h"

ModifiedShowerShape::ModifiedShowerShape(PositionCalc calc)
: posCalcLog_(calc) {}

double ModifiedShowerShape::totEnergy(const std::vector<std::pair<DetId,float>>& hitFracs,
                                      const EcalRecHitCollection* ecalRecHits) {
  double aEnergy = 0.;

  for (const auto& hitFrac : hitFracs) {
    if (hitFrac.first==DetId(0))
      continue;

    aEnergy += noZS::EcalClusterTools::recHitEnergy(hitFrac.first,ecalRecHits)*hitFrac.second;
  }

  return aEnergy;
}

int ModifiedShowerShape::deltaIeta(const EBDetId& asubdetId, const EBDetId& originSubdetId) {
  int diff = asubdetId.ieta() - originSubdetId.ieta();

  if ( asubdetId.ieta()*originSubdetId.ieta() < 0 ) {
    if ( asubdetId.ieta()>0 )
      diff--;
    else
      diff++;
  }

  return diff;
}

int ModifiedShowerShape::deltaIphi(const EBDetId& asubdetId, const EBDetId& originSubdetId) {
  int diff = asubdetId.iphi() - originSubdetId.iphi();

  if ( diff > 180 )
    diff -= 360;
  else if ( diff < -180 )
    diff += 360;

  return diff;
}

int ModifiedShowerShape::deltaIx(const EEDetId& asubdetId, const EEDetId& originSubdetId) {
  return asubdetId.ix() - originSubdetId.ix();
}

int ModifiedShowerShape::deltaIy(const EEDetId& asubdetId, const EEDetId& originSubdetId) {
  return asubdetId.iy() - originSubdetId.iy();
}

std::pair<int,int> ModifiedShowerShape::estimateDExDPy(const DetId& adetId, const DetId& origindetId) {
  int dEx = 0;
  int dPy = 0;

  if ( origindetId.subdetId()==EcalSubdetector::EcalBarrel && adetId.subdetId()==EcalSubdetector::EcalBarrel ) {
    dEx = deltaIeta( EBDetId(adetId), EBDetId(origindetId) );
    dPy = deltaIphi( EBDetId(adetId), EBDetId(origindetId) );
  } else if ( origindetId.subdetId()==EcalSubdetector::EcalEndcap && adetId.subdetId()==EcalSubdetector::EcalEndcap ) {
    dEx = deltaIx( EEDetId(adetId), EEDetId(origindetId) );
    dPy = deltaIy( EEDetId(adetId), EEDetId(origindetId) );
  } else {
    throw cms::Exception("LogicError") << "EcalRecHit should be either EB or EE!";
  }

  return std::make_pair(dEx,dPy);
}

std::pair<float,float> ModifiedShowerShape::meanPosInLocalCoord(const std::vector<std::pair<DetId,float>>& hitFracs,
                                                                const EcalRecHitCollection* ecalRecHits,
                                                                const DetId& refXtal,
                                                                float w0) {
  double sumW = 0.;
  float meanEx = 0.;
  float meanPy = 0.;

  for (const auto& hitFrac : hitFracs) {
    if (hitFrac.first==DetId(0))
      continue;

    auto dExdPy = estimateDExDPy(hitFrac.first,refXtal);
    float en = noZS::EcalClusterTools::recHitEnergy(hitFrac.first,ecalRecHits)*hitFrac.second;
    double xtalWeight = (en>0.) ? en : 0.;
    sumW += xtalWeight;
    meanEx += xtalWeight*static_cast<float>(dExdPy.first);
    meanPy += xtalWeight*static_cast<float>(dExdPy.second);
  }

  return std::make_pair(meanEx/sumW,meanPy/sumW);
}

std::tuple<double,double,double> ModifiedShowerShape::calcSigmas(const reco::GsfElectron& aEle,
                                                                 const std::vector<std::pair<DetId,float>>& hitFracs,
                                                                 const EcalRecHitCollection* ecalRecHits,
                                                                 double sumE,
                                                                 float w0) {
  auto meanDExDPy = meanPosInLocalCoord(hitFracs,ecalRecHits,aEle.superCluster()->seed()->seed());
  double sigEE = 0.;
  double sigEP = 0.;
  double sigPP = 0.;
  double sumW = 0.;

  for (const auto& hitFrac : hitFracs) {
    if (hitFrac.first==DetId(0))
      continue;

    float en = noZS::EcalClusterTools::recHitEnergy(hitFrac.first,ecalRecHits)*hitFrac.second;
    double xtalWeight = (en>0.) ? std::max( 0., static_cast<double>(w0) + std::log(en/sumE) ) : 0.;
    auto dExdPy = estimateDExDPy(hitFrac.first,aEle.superCluster()->seed()->seed());
    float dEx = static_cast<float>(dExdPy.first) - meanDExDPy.first;
    float dPy = static_cast<float>(dExdPy.second) - meanDExDPy.second;
    sumW += xtalWeight;
    sigEE += xtalWeight*dEx*dEx;
    sigPP += xtalWeight*dPy*dPy;
    sigEP += xtalWeight*dEx*dPy;
  }

  return std::make_tuple(sigEE/sumW,sigEP/sumW,sigPP/sumW);
}

ModifiedShowerShape::variables ModifiedShowerShape::value(const reco::GsfElectron& aEle,
                                                          const EcalRecHitCollection* ecalRecHits,
                                                          const double dEtaInSeed2nd,
                                                          const double dPhiInSC2nd,
                                                          const edm::EventSetup& iSetup) {
  // Get Calo Geometry
  edm::ESHandle<CaloGeometry> caloGeoHandle;
  iSetup.get<CaloGeometryRecord>().get(caloGeoHandle);
  const CaloGeometry* caloGeom = caloGeoHandle.product();

  // Get Calo Topology
  edm::ESHandle<CaloTopology> caloTopoHandle;
  iSetup.get<CaloTopologyRecord>().get(caloTopoHandle);
  const CaloTopology* caloTopo = caloTopoHandle.product();

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

  const float eta1stGSF = -( aEle.deltaEtaSeedClusterTrackAtVtx() - aEle.superCluster()->seed()->eta() );
  const float phi1stGSF = reco::reduceRange( -( aEle.deltaPhiSuperClusterTrackAtVtx() - aEle.superCluster()->phi() ) );
  const float eta2ndGSF = -( dEtaInSeed2nd - aEle.superCluster()->seed()->eta() );
  const float phi2ndGSF = reco::reduceRange( -( dPhiInSC2nd - aEle.superCluster()->phi() ) );

  const DetId xtal1st = searchClosestXtal(eta1stGSF,phi1stGSF);
  const DetId xtal2nd = searchClosestXtal(eta2ndGSF,phi2ndGSF);

  if ( xtal1st==DetId(0) || xtal2nd==DetId(0) )
    return variables();

  const CaloSubdetectorGeometry* subdetGeom = caloGeom->getSubdetectorGeometry(xtal1st);

  auto matrix5x5of1stGSF = noZS::EcalClusterTools::matrixDetId(caloTopo, xtal1st, 2 );
  auto matrix5x5of2ndGSF = noZS::EcalClusterTools::matrixDetId(caloTopo, xtal2nd, 2 );
  std::vector<DetId> unionMatrix5x5(matrix5x5of1stGSF);
  std::vector<std::pair<DetId,float>> hitFracUnion5x5;

  for (auto& adetId : matrix5x5of2ndGSF) {
    if ( std::find(unionMatrix5x5.begin(),unionMatrix5x5.end(),adetId)==unionMatrix5x5.end() )
      unionMatrix5x5.push_back(adetId);
  }

  for (const auto& recHit : *ecalRecHits) {
    if ( std::find(unionMatrix5x5.begin(),unionMatrix5x5.end(),recHit.detid())!=unionMatrix5x5.end() )
      hitFracUnion5x5.push_back(std::make_pair(recHit.detid(),1.));
  }

  auto posUnion5x5Log = posCalcLog_.Calculate_Location(hitFracUnion5x5,ecalRecHits,subdetGeom);
  double sumE = totEnergy(hitFracUnion5x5,ecalRecHits);

  auto sigmas = calcSigmas(aEle,hitFracUnion5x5,ecalRecHits,sumE);
  double covEE = std::get<0>(sigmas);
  double covEP = std::get<1>(sigmas);
  double covPP = std::get<2>(sigmas);
  double alpha = std::atan( (covEE - covPP + std::sqrt( (covPP - covEE)*(covPP - covEE) + 4.*covEP*covEP )) / (2.*covEP) );

  double dEtaInUnion5x5 = posUnion5x5Log.eta() - eta1stGSF;
  double dPhiInUnion5x5 = reco::deltaPhi(posUnion5x5Log.phi(),phi1stGSF);
  double union5x5Energy = totEnergy(hitFracUnion5x5,ecalRecHits);

  return variables(covEE,covEP,covPP,alpha,dEtaInUnion5x5,dPhiInUnion5x5,union5x5Energy);
}

ModifiedShowerShape::variables ModifiedShowerShape::value(const reco::GsfElectron& aEle,
                                                          const EcalRecHitCollection* ecalRecHits,
                                                          const edm::EventSetup& iSetup) {
  // Get Calo Geometry
  edm::ESHandle<CaloGeometry> caloGeoHandle;
  iSetup.get<CaloGeometryRecord>().get(caloGeoHandle);
  const CaloGeometry* caloGeom = caloGeoHandle.product();

  // Get Calo Topology
  edm::ESHandle<CaloTopology> caloTopoHandle;
  iSetup.get<CaloTopologyRecord>().get(caloTopoHandle);
  const CaloTopology* caloTopo = caloTopoHandle.product();

  const float eta1stGSF = -( aEle.deltaEtaSeedClusterTrackAtVtx() - aEle.superCluster()->seed()->eta() );
  const float phi1stGSF = reco::reduceRange( -( aEle.deltaPhiSuperClusterTrackAtVtx() - aEle.superCluster()->phi() ) );

  const DetId xtal1st = aEle.superCluster()->seed()->seed();

  if ( xtal1st==DetId(0) )
    return variables();

  const CaloSubdetectorGeometry* subdetGeom = caloGeom->getSubdetectorGeometry(xtal1st);

  auto matrix5x5of1stGSF = noZS::EcalClusterTools::matrixDetId(caloTopo, xtal1st, 2 );
  std::vector<DetId> unionMatrix5x5(matrix5x5of1stGSF);
  std::vector<std::pair<DetId,float>> hitFracUnion5x5;

  for (const auto& recHit : *ecalRecHits) {
    if ( std::find(unionMatrix5x5.begin(),unionMatrix5x5.end(),recHit.detid())!=unionMatrix5x5.end() )
      hitFracUnion5x5.push_back(std::make_pair(recHit.detid(),1.));
  }

  double sumE = totEnergy(hitFracUnion5x5,ecalRecHits);
  auto sigmas = calcSigmas(aEle,hitFracUnion5x5,ecalRecHits,sumE);
  double covEE = std::get<0>(sigmas);
  double covEP = std::get<1>(sigmas);
  double covPP = std::get<2>(sigmas);
  double alpha = std::atan( (covEE - covPP + std::sqrt( (covPP - covEE)*(covPP - covEE) + 4.*covEP*covEP )) / (2.*covEP) );

  auto posUnion5x5Log = posCalcLog_.Calculate_Location(hitFracUnion5x5,ecalRecHits,subdetGeom);
  double dEtaInUnion5x5 = posUnion5x5Log.eta() - eta1stGSF;
  double dPhiInUnion5x5 = reco::deltaPhi(posUnion5x5Log.phi(),phi1stGSF);
  double union5x5Energy = totEnergy(hitFracUnion5x5,ecalRecHits);

  return variables(covEE,covEP,covPP,alpha,dEtaInUnion5x5,dPhiInUnion5x5,union5x5Energy);
}
