import FWCore.ParameterSet.Config as cms
from RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_tools import *

# same with official ones but w/o PF isolation
def configureVIDModifiedCutBasedEleID_V5( wpEB, wpEE ):
    parameterSet =  cms.PSet(
        idName = cms.string( wpEB.idName ), # same name stored in the _EB and _EE objects
        cutFlow = cms.VPSet(
            psetMinPtCut(),
            psetPhoSCEtaMultiRangeCut(),                        # eta cut
            psetDEtaInSeedCut(wpEB, wpEE),                      # dEtaIn seed cut
            psetDPhiInCut(wpEB, wpEE),                          # dPhiIn cut
            psetPhoFull5x5SigmaIEtaIEtaCut(wpEB, wpEE),         # full 5x5 sigmaIEtaIEta cut
            psetHadronicOverEMEnergyScaledCut(wpEB, wpEE),      # H/E cut
            psetEInerseMinusPInverseCut(wpEB, wpEE),            # |1/e-1/p| cut
            psetConversionVetoCut(),
            psetMissingHitsCut(wpEB, wpEE)
            )
        )

    return parameterSet
