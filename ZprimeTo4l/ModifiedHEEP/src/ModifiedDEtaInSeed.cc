#include "ZprimeTo4l/ModifiedHEEP/interface/ModifiedDEtaInSeed.h"

#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/Math/interface/deltaPhi.h"

#include "Geometry/CaloGeometry/interface/CaloGeometry.h"
#include "Geometry/CaloGeometry/interface/CaloCellGeometry.h"
#include "Geometry/Records/interface/CaloGeometryRecord.h"

#include "Geometry/CaloTopology/interface/CaloTopology.h"
#include "Geometry/CaloEventSetup/interface/CaloTopologyRecord.h"
#include "RecoEcal/EgammaCoreTools/interface/EcalClusterTools.h"
#include "DataFormats/EcalDetId/interface/EcalSubdetector.h"

#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "Geometry/Records/interface/TrackerDigiGeometryRecord.h"
#include "TrackingTools/GsfTools/interface/MultiTrajectoryStateMode.h"
#include "TrackingTools/GsfTools/interface/MultiTrajectoryStateTransform.h"
#include "TrackingTools/GsfTools/interface/GsfPropagatorAdapter.h"
#include "TrackingTools/GeomPropagators/interface/StateOnTrackerBound.h"
#include "TrackingTools/GeomPropagators/interface/AnalyticalPropagator.h"
#include "TrackingTools/TrajectoryState/interface/TrajectoryStateOnSurface.h"
#include "TrackingTools/PatternTools/interface/TransverseImpactPointExtrapolator.h"
#include "MagneticField/Engine/interface/MagneticField.h"
#include "MagneticField/Records/interface/IdealMagneticFieldRecord.h"
#include "RecoEgamma/EgammaElectronAlgos/interface/ElectronUtilities.h"
#include "RecoTracker/Record/interface/TrackerRecoGeometryRecord.h"
#include "RecoTracker/TkDetLayers/interface/GeometricSearchTracker.h"

ModifiedDEtaInSeed::ModifiedDEtaInSeed(PositionCalc calc)
: posCalcLog_(calc) {}

bool ModifiedDEtaInSeed::extrapolate(const reco::GsfElectron& aEle, const reco::TrackBase& addTrk,
                                     const math::XYZPoint& beamSpotPos, const edm::EventSetup& iSetup,
                                     EleRelPointPair& scAtVtx, EleRelPointPair& seedAtCalo) {
  // track-cluster matching (see RecoEgamma/EgammaElectronAlgos/src/GsfElectronAlgo.cc)
  edm::ESHandle<MagneticField> magFieldHandle;
  iSetup.get<IdealMagneticFieldRecord>().get(magFieldHandle);

  // at innermost/outermost point
  // edm::ESHandle<TrackerGeometry> trackerHandle;
  // iSetup.get<TrackerDigiGeometryRecord>().get(trackerHandle);
  // auto mtsTransform = std::make_unique<MultiTrajectoryStateTransform>(trackerHandle.product(),magFieldHandle.product());
  // TrajectoryStateOnSurface innTSOS = mtsTransform->innerStateOnSurface(*addGsfTrk);
  // TrajectoryStateOnSurface outTSOS = mtsTransform->outerStateOnSurface(*addGsfTrk);

  // unfortunately above requires trackExtra - which is only available in RECO
  // instead we start from track vtx then propagate free state to inner/outer surface
  // no recHit hence make a reasonable approximation that
  // inner surface is pixel barrel & outer surface is tracker envelope

  edm::ESHandle<GeometricSearchTracker> trackerSearchHandle;
  iSetup.get<TrackerRecoGeometryRecord>().get(trackerSearchHandle);

  const auto& pixelBarrelLayers = trackerSearchHandle.product()->pixelBarrelLayers();
  BarrelDetLayer* innermostLayer = nullptr;
  float innermostRadius = std::numeric_limits<float>::max();

  for (const auto* alayer : pixelBarrelLayers) {
    float aradius = alayer->surface().rSpan().first;
    if ( aradius < innermostRadius ) {
      innermostRadius = aradius;
      innermostLayer = const_cast<BarrelDetLayer*>(alayer);
    }
  }

  // GlobalTag matters here (tracker alignment)
  FreeTrajectoryState freestate(GlobalTrajectoryParameters(GlobalPoint(addTrk.referencePoint().x(),
                                                                       addTrk.referencePoint().y(),
                                                                       addTrk.referencePoint().z()),
                                                           GlobalVector(addTrk.momentum().x(),
                                                                        addTrk.momentum().y(),
                                                                        addTrk.momentum().z()),
                                                           addTrk.charge(),
                                                           magFieldHandle.product()),
                                CurvilinearTrajectoryError(addTrk.covariance()));
  auto gsfPropagator = std::make_unique<GsfPropagatorAdapter>(AnalyticalPropagator(magFieldHandle.product()));
  auto extrapolator = std::make_unique<TransverseImpactPointExtrapolator>(*gsfPropagator);
  TrajectoryStateOnSurface innTSOS = gsfPropagator->propagate(freestate,innermostLayer->surface());
  StateOnTrackerBound stateOnBound(gsfPropagator.get());
  TrajectoryStateOnSurface outTSOS = stateOnBound(freestate);

  if ( innTSOS.isValid() && outTSOS.isValid() ) {
    // at seed
    TrajectoryStateOnSurface seedTSOS = extrapolator->extrapolate(*(outTSOS.freeState()), // with TSOS assert fails (not a real measurement)
                                                                  GlobalPoint(aEle.superCluster()->seed()->position().x(),
                                                                              aEle.superCluster()->seed()->position().y(),
                                                                              aEle.superCluster()->seed()->position().z()));
    if (!seedTSOS.isValid())
      seedTSOS = outTSOS;

    TrajectoryStateOnSurface sclTSOS = extrapolator->extrapolate(*(innTSOS.freeState()), // with TSOS assert fails (not a real measurement)
                                                                 GlobalPoint(aEle.superCluster()->x(),
                                                                             aEle.superCluster()->y(),
                                                                             aEle.superCluster()->z()));
    if (!sclTSOS.isValid())
      sclTSOS = outTSOS;

    GlobalPoint seedPos, sclPos;
    multiTrajectoryStateMode::positionFromModeCartesian(seedTSOS,seedPos);
    multiTrajectoryStateMode::positionFromModeCartesian(sclTSOS,sclPos);

    scAtVtx = EleRelPointPair(aEle.superCluster()->position(),sclPos,beamSpotPos);
    seedAtCalo = EleRelPointPair(aEle.superCluster()->seed()->position(),seedPos,beamSpotPos);

    return true;
  }

  return false;
}

ModifiedDEtaInSeed::variables ModifiedDEtaInSeed::value(const reco::GsfElectron& aEle,
                                                        const EcalRecHitCollection* ecalRecHits,
                                                        const reco::TrackBase& addTrk,
                                                        const reco::BeamSpot& beamSpot,
                                                        const edm::EventSetup& iSetup) {
  double dEtaInSeed2nd = std::numeric_limits<float>::max();
  double dPhiInSC2nd = std::numeric_limits<float>::max();

  auto scAtVtx = EleRelPointPair(math::XYZPoint(),math::XYZPoint(),beamSpot.position());
  auto seedAtCalo = EleRelPointPair(math::XYZPoint(),math::XYZPoint(),beamSpot.position());

  if ( extrapolate(aEle,addTrk,beamSpot.position(),iSetup,scAtVtx,seedAtCalo) ) {
    dPhiInSC2nd = scAtVtx.dPhi();
    dEtaInSeed2nd = scAtVtx.dEta() - aEle.superCluster()->eta() + aEle.superCluster()->seed()->eta();
  }

  if ( dEtaInSeed2nd==std::numeric_limits<float>::max() || dPhiInSC2nd==std::numeric_limits<float>::max() )
    return variables();

  const float eta1stGSF = -( aEle.deltaEtaSeedClusterTrackAtVtx() - aEle.superCluster()->seed()->eta() );
  const float phi1stGSF = reco::reduceRange( -( aEle.deltaPhiSuperClusterTrackAtVtx() - aEle.superCluster()->phi() ) );
  const float eta2ndGSF = -( dEtaInSeed2nd - aEle.superCluster()->seed()->eta() );
  const float phi2ndGSF = reco::reduceRange( -( dPhiInSC2nd - aEle.superCluster()->phi() ) );

  // estimate alpha track
  const float dEtaCalo = eta2ndGSF - eta1stGSF;
  const float dPhiCalo = reco::deltaPhi( phi2ndGSF , phi1stGSF );
  const double drCalo = std::hypot( dEtaCalo, dPhiCalo );
  const double alphaTrack = std::asin( static_cast<double>(dEtaCalo)/drCalo );

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

  const DetId xtal1st = searchClosestXtal(eta1stGSF,phi1stGSF);
  const DetId xtal2nd = searchClosestXtal(eta2ndGSF,phi2ndGSF);

  if ( xtal1st==DetId(0) || xtal2nd==DetId(0) )
    return variables(std::numeric_limits<float>::max(),dEtaInSeed2nd,dPhiInSC2nd,alphaTrack,std::numeric_limits<float>::max());

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

  // u = dEtaCalo*cos(alpha) + dPhiCalo*sin(alpha) = 0 (perpendicular component)
  // v = dEtaCalo*sin(alpha) - dPhiCalo*cos(alpha) = drCalo (parallel component)
  double cosAlpha = -dPhiCalo/drCalo;
  double sinAlpha = dEtaCalo/drCalo;
  double dEtaInUnion5x5 = posUnion5x5Log.eta() - eta1stGSF;
  double dPhiInUnion5x5 = reco::deltaPhi(posUnion5x5Log.phi(),phi1stGSF);

  double union5x5U = dEtaInUnion5x5*cosAlpha + dPhiInUnion5x5*sinAlpha;
  double union5x5V = dEtaInUnion5x5*sinAlpha - dPhiInUnion5x5*cosAlpha;

  return variables(union5x5U,dEtaInSeed2nd,dPhiInSC2nd,alphaTrack,union5x5V/drCalo);
}
