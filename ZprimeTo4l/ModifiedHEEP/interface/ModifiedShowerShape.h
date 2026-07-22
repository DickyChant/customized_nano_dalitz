#ifndef ModifiedShowerShape_h
#define ModifiedShowerShape_h 1

#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/EcalRecHit/interface/EcalRecHitCollections.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "RecoEcal/EgammaCoreTools/interface/PositionCalc.h"

class ModifiedShowerShape {
public:
  ModifiedShowerShape(PositionCalc calc);
  ~ModifiedShowerShape()=default;

  struct variables {
    variables()
    : covEE(std::numeric_limits<float>::max()),
      covEP(std::numeric_limits<float>::max()),
      covPP(std::numeric_limits<float>::max()),
      alpha(std::numeric_limits<float>::max()),
      dEtaInUnion5x5(std::numeric_limits<float>::max()),
      dPhiInUnion5x5(std::numeric_limits<float>::max()),
      union5x5Energy(0.) {}

    variables(const double cee, const double cep, const double cpp, const double alp,
              const double dein, const double dpin, const double en)
    : covEE(cee),
      covEP(cep),
      covPP(cpp),
      alpha(alp),
      dEtaInUnion5x5(dein),
      dPhiInUnion5x5(dpin),
      union5x5Energy(en) {}

    double covEE;
    double covEP;
    double covPP;
    double alpha;
    double dEtaInUnion5x5;
    double dPhiInUnion5x5;
    double union5x5Energy;
  };

  variables value(const reco::GsfElectron& aEle,
                  const EcalRecHitCollection* ecalRecHits,
                  const double dEtaInSeed2nd,
                  const double dPhiInSC2nd,
                  const edm::EventSetup& iSetup);

  variables value(const reco::GsfElectron& aEle,
                  const EcalRecHitCollection* ecalRecHits,
                  const edm::EventSetup& iSetup);

  double totEnergy(const std::vector<std::pair<DetId,float>>& hitFracs,
                   const EcalRecHitCollection* ecalRecHits);

  int deltaIeta(const EBDetId& asubdetId, const EBDetId& originSubdetId);
  int deltaIphi(const EBDetId& asubdetId, const EBDetId& originSubdetId);
  int deltaIx(const EEDetId& asubdetId, const EEDetId& originSubdetId);
  int deltaIy(const EEDetId& asubdetId, const EEDetId& originSubdetId);

  std::pair<int,int> estimateDExDPy(const DetId& adetId, const DetId& origindetId);
  std::pair<float,float> meanPosInLocalCoord(const std::vector<std::pair<DetId,float>>& hitFracs,
                                             const EcalRecHitCollection* ecalRecHits,
                                             const DetId& refXtal,
                                             float w0=4.7);
  std::tuple<double,double,double> calcSigmas(const reco::GsfElectron& aEle,
                                              const std::vector<std::pair<DetId,float>>& hitFracs,
                                              const EcalRecHitCollection* ecalRecHits,
                                              double sumE,
                                              float w0=4.7);

private:
  PositionCalc posCalcLog_;
};

#endif
