#ifndef ZprimeTo4l_ModifiedHEEP_ModifiedEleTkIsoFromCands_H
#define ZprimeTo4l_ModifiedHEEP_ModifiedEleTkIsoFromCands_H 1

#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ParameterSet/interface/ParameterSetDescription.h"

#include "FWCore/Framework/interface/EventSetup.h"

#include "DataFormats/TrackReco/interface/TrackBase.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectronFwd.h"
#include "DataFormats/GsfTrackReco/interface/GsfTrack.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/PatCandidates/interface/Electron.h"

//author S. Harper (RAL)
//this class does a simple calculation of the track isolation for a track with eta,
//phi and z vtx (typically the GsfTrack of the electron). It uses
//PFPackedCandidates as proxies for the tracks. It now has been upgraded to
//take general tracks as input also
//
//Note: due to rounding and space saving issues, the isolation calculated on tracks and
//PFPackedCandidates will differ slightly even if the same cuts are used. These differences
//are thought to be inconsquencial but as such its important to remake the PFPackedCandidates
//in RECO/AOD if you want to be consistant with miniAOD
//
//The track version is more for variables that are stored in the electron rather than
//objects which are recomputed on the fly for AOD/miniAOD
//
//Note, the tracks in miniAOD have additional cuts on and are missing algo information so this
//has to be taken into account when using them

//new for 9X:
//  1) its now possible to use generalTracks as input
//  2) adapted to 9X PF packed candidate improvements
//  2a) the PF packed candidates now store the pt of the track in addition to the pt of the
//      candidate. This means there is no need to pass in the electron collection any more
//      to try and undo the electron e/p combination when the candidate is an electron
//  2b) we now not only store the GsfTrack of the electron but also the general track of the electron
//      there are three input collections now:
//         packedPFCandidates : all PF candidates (with the track for ele candidates being the gsftrack)
//         lostTracks : all tracks which were not made into a PFCandidate but passed some preselection
//         lostTracks::eleTracks : KF electron tracks
//      as such to avoid double counting the GSF and KF versions of an electron track, we now need to
//      specify if the electron PF candidates are to be rejected in the sum over that collection or not.
//      Note in all this, I'm not concerned about the electron in questions track, that will be rejected,
//      I'm concerned about near by fake electrons which have been recoed by PF
//      This is handled by the PIDVeto, which obviously is only used/required when using PFCandidates

class ModifiedEleTkIsolFromCands {
public:
  enum class PIDVeto {
    NONE=0,
    ELES,
    NONELES,
  };

  struct TrkCuts {
    float minPt;
    float minDR2;
    float maxDR2;
    float minDEta;
    float dEta2nd;
    float dPhi2nd;
    float maxDZ;
    float minHits;
    float minPixelHits;
    float maxDPtPt;
    float addTrkMinPt;
    float addTrkDR2;
    float addTrkREguard;
    float addTrkHoE;
    std::vector<reco::TrackBase::TrackQuality> allowedQualities;
    std::vector<reco::TrackBase::TrackAlgorithm> algosToReject;
    explicit TrkCuts(const edm::ParameterSet& para);
    static edm::ParameterSetDescription pSetDescript();
  };

  TrkCuts barrelCuts_,endcapCuts_;

  explicit ModifiedEleTkIsolFromCands(const edm::ParameterSet& para);
  ModifiedEleTkIsolFromCands(const ModifiedEleTkIsolFromCands&)=default;
  ~ModifiedEleTkIsolFromCands()=default;
  ModifiedEleTkIsolFromCands& operator=(const ModifiedEleTkIsolFromCands&)=default;

  double calIsol(const reco::TrackBase& trk,
                 const edm::Handle<edm::View<pat::PackedCandidate>>& cands,
                 const reco::TrackBase& addTrk,
                 const PIDVeto=PIDVeto::NONE) const;
  double calIsol(const double eleEta,
                 const double elePhi,
                 const double eleVZ,
                 const edm::Handle<edm::View<pat::PackedCandidate>>& cands,
                 const reco::TrackBase& addTrk,
                 const PIDVeto=PIDVeto::NONE)const;

  double calIsol(const reco::TrackBase& trk, const reco::TrackCollection& tracks, const reco::TrackBase& addTrk) const;
  double calIsol(const double eleEta,
                 const double elePhi,
                 const double eleVZ,
                 const reco::TrackCollection& tracks,
                 const reco::TrackBase& addTrk) const;

  //little helper function for the four calIsol functions for it to directly return the pt
  template<typename ...Args>
  double calIsolPt(Args && ...args) const { return calIsol(std::forward<Args>(args)...); }

  static PIDVeto pidVetoFromStr(const std::string& vetoStr);
  static bool passPIDVeto(const int pdgId, const ModifiedEleTkIsolFromCands::PIDVeto pidVeto);

  bool additionalTrkSel(const reco::TrackBase& addTrk,
                        const reco::TrackBase& eleTrk,
                        const TrkCuts& cuts);
  bool additionalTrkSel(const edm::RefToBase<pat::PackedCandidate>& cand,
                        const reco::TrackBase& eleTrk,
                        const TrkCuts& cuts);

  const reco::GsfTrackRef additionalGsfTrkSelector(const reco::GsfElectron& ele,
                                                   const edm::Handle<edm::View<reco::GsfTrack>>& gsfTrks,
                                                   const edm::EventSetup& iSetup);
  const pat::PackedCandidateRef additionalPackedCandSelector(const pat::Electron& ele,
                                                             const std::vector<edm::Handle<edm::View<pat::PackedCandidate>>>& cands,
                                                             const std::vector<ModifiedEleTkIsolFromCands::PIDVeto>& candVetos,
                                                             const edm::EventSetup& iSetup);

private:
  static bool passTrkSel(const reco::TrackBase& trk,
                         const double trkPt,
                         const TrkCuts& cuts,
                         const double eleEta,
                         const double elePhi,
                         const double eleVZ);
  //no qualities specified, accept all, ORed

  static bool passQual(const reco::TrackBase& trk, const std::vector<reco::TrackBase::TrackQuality>& quals);
  static bool passAlgo(const reco::TrackBase& trk, const std::vector<reco::TrackBase::TrackAlgorithm>& algosToRej);
};


#endif
