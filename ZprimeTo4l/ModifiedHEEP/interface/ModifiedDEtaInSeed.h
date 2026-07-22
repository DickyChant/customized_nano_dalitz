#ifndef ModifiedDEtaInSeed_h
#define ModifiedDEtaInSeed_h 1

#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/EcalRecHit/interface/EcalRecHitCollections.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "RecoEcal/EgammaCoreTools/interface/PositionCalc.h"
#include "RecoEgamma/EgammaElectronAlgos/interface/ElectronUtilities.h"

class ModifiedDEtaInSeed {
public:
  ModifiedDEtaInSeed(PositionCalc calc);
  ~ModifiedDEtaInSeed()=default;

  struct variables {
    variables()
    : dPerpIn(std::numeric_limits<float>::max()),
      dEtaInSeed2nd(std::numeric_limits<float>::max()),
      dPhiInSC2nd(std::numeric_limits<float>::max()),
      alphaTrack(std::numeric_limits<float>::max()),
      normalizedDParaIn(std::numeric_limits<float>::max()) {}

    variables(const double dPerp, const double dEta2nd, const double dPhi2nd,
              const double alTrk, const double dPara)
    : dPerpIn(dPerp),
      dEtaInSeed2nd(dEta2nd),
      dPhiInSC2nd(dPhi2nd),
      alphaTrack(alTrk),
      normalizedDParaIn(dPara) {}

    double dPerpIn;
    double dEtaInSeed2nd;
    double dPhiInSC2nd;
    double alphaTrack;
    double normalizedDParaIn;
  };

  variables value(const reco::GsfElectron& aEle,
                  const EcalRecHitCollection* ecalRecHits,
                  const reco::TrackBase& addTrk,
                  const reco::BeamSpot& beamSpot,
                  const edm::EventSetup& iSetup);

  bool extrapolate(const reco::GsfElectron& aEle, const reco::TrackBase& addTrk,
                   const math::XYZPoint& beamSpotPos, const edm::EventSetup& iSetup,
                   EleRelPointPair& scAtVtx, EleRelPointPair& seedAtCalo);

private:
  PositionCalc posCalcLog_;
};

#endif
