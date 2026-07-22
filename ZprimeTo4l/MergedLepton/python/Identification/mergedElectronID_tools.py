import FWCore.ParameterSet.Config as cms
from RecoEgamma.ElectronIdentification.Identification.heepElectronID_tools import *
from ZprimeTo4l.ModifiedHEEP.Identification.modifiedHeepElectronID_tools import *

def configureMergedElectronID(mvaWP, moduleEra=""):
    pSet = cms.PSet(
        idName = cms.string( mvaWP.idName ),
        cutFlow = cms.VPSet(
            # merged electron MVA ID
            cms.PSet(
                cutName = cms.string("GsfEleMVACut"),
                mvaCuts = cms.vstring( mvaWP.getCutStrings() ),
                mvaValueMapName = cms.InputTag( "mergedLeptonIDProducer"+moduleEra+":mvaMergedElectronValues" ),
                mvaCategoriesMapName = cms.InputTag( "mergedLeptonIDProducer"+moduleEra+":mvaMergedElectronCategories" ),
                needsAdditionalProducts = cms.bool(True),
                isIgnored = cms.bool(False)
            ),
            cms.PSet(
                cutName = cms.string('GsfEleDPtOverPtCut'),
                dPtOverPtCutValue = cms.double( 0.5 ),
                addGsfTrk = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddGsfTrk"),
                addPackedCand = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddPackedCand"),
                needsAdditionalProducts = cms.bool(True),
                isIgnored = cms.bool(False)
            )
        )
    )

    return pSet
