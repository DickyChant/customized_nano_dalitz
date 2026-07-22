import FWCore.ParameterSet.Config as cms
from RecoEgamma.ElectronIdentification.Identification.mvaElectronID_tools import EleMVA_WP
from ZprimeTo4l.MergedLepton.Identification.mergedElectronID_tools import configureMergedElectronID

mvaMergedElectron_20UL16_container = EleMVA_WP(
    idName = "mvaMergedElectron",
    mvaTag = "", # never used since we hacked ValueMap names
    cutCategory0 = "0.606", # HasTrk
    cutCategory1 = "0.667", # NoTrkEt2
)

# let's make a chimera of cutflow & MVA ID
mvaMergedElectron_20UL16 = configureMergedElectronID( mvaMergedElectron_20UL16_container )
mvaMergedElectron_20UL16.isPOGApproved = cms.untracked.bool(False)
