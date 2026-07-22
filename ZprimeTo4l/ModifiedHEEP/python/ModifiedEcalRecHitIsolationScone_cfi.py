import FWCore.ParameterSet.Config as cms
import RecoEgamma.EgammaElectronProducers.gedGsfElectrons_cfi as gedGsfEle
from ZprimeTo4l.ModifiedHEEP.ModifiedElectronTrackIsolations_cfi import trkIsol03CfgV2

stdGsfEle = gedGsfEle.gedGsfElectronsTmp

ModifiedEcalRecHitIsolationScone = cms.EDProducer("ModifiedEcalRecHitIsolationProducer",
    ecalBarrelRecHitCollection = cms.InputTag("reducedEgamma","reducedEBRecHits"),
    ecalEndcapRecHitCollection = cms.InputTag("reducedEgamma","reducedEERecHits"),

    useNumCrystals = cms.bool(True),
    intRadiusBarrel = cms.double(3.0),
    intRadiusEndcap = cms.double(3.0),
    jurassicWidth = cms.double(1.5), #dEta strip width
    extRadius = cms.double(0.3),
    etMinBarrel = cms.double(0.0),
    eMinBarrel = cms.double(0.095),
    etMinEndcap = cms.double(0.110),
    eMinEndcap = cms.double(0.0),

    useIsolEt = cms.bool(True),
    tryBoth   = cms.bool(True),
    subtract  = cms.bool(False),
    vetoClustered  = cms.bool(False),

    emObjectProducer = cms.InputTag("slimmedElectrons","","PAT"),

    recHitFlagsExclBarrel = stdGsfEle.recHitFlagsToBeExcludedBarrel,
    recHitFlagsExclEndcaps = stdGsfEle.recHitFlagsToBeExcludedEndcaps,
    recHitSeverityExclBarrel = stdGsfEle.recHitSeverityToBeExcludedBarrel,
    recHitSeverityExclEndcaps = stdGsfEle.recHitSeverityToBeExcludedEndcaps,

    addGsfTrkMap = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddGsfTrk"),
    addPackedCandMap = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddPackedCand"),
    dEtaInSeed2nd = cms.InputTag("ModifiedHEEPIDVarValueMaps","dEtaInSeed2nd"),
    dPhiInSC2nd = cms.InputTag("ModifiedHEEPIDVarValueMaps","dPhiInSC2nd")
)
