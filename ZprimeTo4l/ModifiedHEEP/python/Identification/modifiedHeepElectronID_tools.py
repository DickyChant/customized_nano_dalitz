import FWCore.ParameterSet.Config as cms
from RecoEgamma.ElectronIdentification.Identification.heepElectronID_tools import *

# copied from psetGsfEleTrkPtFall16IsoCut
def psetGsfModifiedEleTrkPtIsoCut(wpEB, wpEE):
    return cms.PSet(
        cutName = cms.string('GsfEleValueMapIsoRhoCut'),
        # Three constants for the GsfEleTrkPtIsoCut
        #     cut = constTerm if value < slopeStart
        #     cut = slopeTerm * (value - slopeStart) + constTerm if value >= slopeStart
        slopeTermEB = cms.double( wpEB.trkIsoSlopeTerm ),
        slopeTermEE = cms.double( wpEE.trkIsoSlopeTerm ),
        slopeStartEB = cms.double( wpEB.trkIsoSlopeStart ),
        slopeStartEE = cms.double( wpEE.trkIsoSlopeStart ),
        constTermEB = cms.double( wpEB.trkIsoConstTerm ),
        constTermEE = cms.double( wpEE.trkIsoConstTerm ),
        #no rho so we zero it out, if the input tag is empty, its ignored anyways
        rhoEtStartEB = cms.double( 999999. ),
        rhoEtStartEE = cms.double( 999999. ),
        rhoEAEB = cms.double( 0. ),
        rhoEAEE = cms.double( 0. ),
        rho = cms.InputTag(""),
        value = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleTrkPtIso"),
        needsAdditionalProducts = cms.bool(True),
        isIgnored = cms.bool(False)
        )

def psetGsfModifiedEleEmHadD1IsoRhoCut(wpEB, wpEE, energyType="EcalTrk"):
    return cms.PSet(
        cutName = cms.string('GsfEleModifiedEmHadD1IsoRhoCut'),
        slopeTermEB = cms.double( wpEB.ehIsoSlopeTerm ),
        slopeTermEE = cms.double( wpEE.ehIsoSlopeTerm ),
        slopeStartEB = cms.double( wpEB.ehIsoSlopeStart ),
        slopeStartEE = cms.double( wpEE.ehIsoSlopeStart ),
        constTermEB = cms.double( wpEB.ehIsoConstTerm ),
        constTermEE = cms.double( wpEE.ehIsoConstTerm ),
        energyType = cms.string( energyType ),
        rhoConstant = cms.double( wpEB.effAreaForEHIso ), # expected to be the same for EB and EE
        rho = cms.InputTag("fixedGridRhoFastjetAll"),
        value = cms.InputTag("ModifiedEcalRecHitIsolationScone","EcalRecHitIso"),
        addGsfTrk = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddGsfTrk"),
        addPackedCand = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddPackedCand"),
        needsAdditionalProducts = cms.bool(True),
        isIgnored = cms.bool(False)
        )

def psetGsfModifiedEleDEtaInSeedCut(wpEB, wpEE):
    return cms.PSet(
        cutName = cms.string('GsfEleModifiedDEtaInSeedCut'),
        dEtaInSeedCutValueEB = cms.double( wpEB.dEtaInSeedCut ),
        dEtaInSeedCutValueEE = cms.double( wpEE.dEtaInSeedCut ),
        modifiedDEtaInSeedCutValueEB = cms.double( 0.004 ),
        barrelCutOff = cms.double( 1.479 ),
        addGsfTrk = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddGsfTrk"),
        addPackedCand = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddPackedCand"),
        modifiedDEtaInSeed = cms.InputTag("ModifiedHEEPIDVarValueMaps","dPerpIn"),
        needsAdditionalProducts = cms.bool(True),
        isIgnored = cms.bool(False)
        )

def psetGsfModifiedEleFull5x5E2x5OverE5x5WithSatCut(wpEB, wpEE):
    return cms.PSet(
        cutName = cms.string('GsfEleModifiedFull5x5E2x5OverE5x5WithSatCut'),
        # E1x5 / E5x5
        minE1x5OverE5x5EB = cms.double( wpEB.minE1x5OverE5x5Cut ),
        minE1x5OverE5x5EE = cms.double( wpEE.minE1x5OverE5x5Cut ),
        # E2x5 / E5x5
        minE2x5OverE5x5EB = cms.double( wpEB.minE2x5OverE5x5Cut ),
        minE2x5OverE5x5EE = cms.double( wpEE.minE2x5OverE5x5Cut ),
        maxNrSatCrysIn5x5EB =cms.int32( 0 ),
        maxNrSatCrysIn5x5EE =cms.int32( 0 ),
        addGsfTrk = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddGsfTrk"),
        addPackedCand = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddPackedCand"),
        needsAdditionalProducts = cms.bool(True),
        isIgnored = cms.bool(False)
        )

def configureModifiedHEEPElectronID(idName, wpEB, wpEE):
    parameterSet = cms.PSet(
        idName = cms.string(idName),
        cutFlow = cms.VPSet(
            psetMinPtCut(cutValue=20.),                   #0
            psetGsfEleSCEtaMultiRangeCut(),               #1
            psetGsfModifiedEleDEtaInSeedCut(wpEB,wpEE),   #2
            psetGsfEleDPhiInCut(wpEB,wpEE),               #3
            psetGsfEleFull5x5SigmaIEtaIEtaWithSatCut(wpEB,wpEE), #4
            psetGsfModifiedEleFull5x5E2x5OverE5x5WithSatCut(wpEB,wpEE),  #5
            psetGsfEleHadronicOverEMLinearCut(wpEB,wpEE), #6
            psetGsfModifiedEleTrkPtIsoCut(wpEB,wpEE),     #7
            psetGsfModifiedEleEmHadD1IsoRhoCut(wpEB,wpEE),#8
            psetGsfEleDxyCut(wpEB,wpEE),                  #9
            psetGsfEleMissingHitsCut(wpEB,wpEE),          #10,
            psetGsfEleEcalDrivenCut(wpEB,wpEE)            #11
            )
        )

    return parameterSet
