#include "DataFormats/Common/interface/Wrapper.h"
#include "DataFormats/Common/interface/ValueMap.h"
#include "DataFormats/GsfTrackReco/interface/GsfTrack.h"
#include "DataFormats/GsfTrackReco/interface/GsfTrackFwd.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include <vector>

namespace ZprimeTo4l_ModifiedHEEP {
  struct dictionary {
    std::vector<reco::GsfTrackRef> v_gsftrkref;
    std::vector<pat::PackedCandidateRef> v_pcref;
    edm::ValueMap<reco::GsfTrackRef> vm_gsftrkref;
    edm::Wrapper<edm::ValueMap<reco::GsfTrackRef> > w_vm_gsftrkref;
    edm::ValueMap<pat::PackedCandidateRef> vm_pcref;
    edm::Wrapper<edm::ValueMap<pat::PackedCandidateRef> > w_vm_pcref;
  };
}
