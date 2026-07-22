import FWCore.ParameterSet.Config as cms

from ZprimeTo4l.ModifiedHEEP.ModifiedElectronTrackIsolations_cfi import trkIsol03CfgV2, trkIsol04CfgV2

ModifiedHEEPIDVarValueMaps = cms.EDProducer("ModifiedHEEPIDValueMapProducer",
    beamSpot = cms.InputTag("offlineBeamSpot"),
    candsAOD = cms.VInputTag("packedCandsForTkIso",
                             "lostTracksForTkIso",
                             "lostTracksForTkIso:eleTracks"),
    #because GsfTracks of electrons are in "packedPFCandidates"
    #end KF tracks of electrons are in lostTracks:eleTracks, need to
    #tell producer to veto electrons in the first collection
    candVetosAOD = cms.vstring("ELES","NONE","NONELES"),
    gsfTrksAOD = cms.InputTag("electronGsfTracks"),
    elesAOD = cms.InputTag("gedGsfElectrons"),
    EBrecHitsAOD = cms.InputTag("EcalRecHitsEB"),
    EErecHitsAOD = cms.InputTag("EcalRecHitsEE"),
    candsMiniAOD = cms.VInputTag("packedPFCandidates",
                                 "lostTracks",
                                 "lostTracks:eleTracks"),
    candVetosMiniAOD = cms.vstring("ELES","NONE","NONELES"),
    gsfTrksMiniAOD = cms.InputTag("reducedEgamma:reducedGsfTracks"),
    elesMiniAOD = cms.InputTag("slimmedElectrons","","PAT"),
    EBrecHitsMiniAOD = cms.InputTag("reducedEgamma","reducedEBRecHits"),
    EErecHitsMiniAOD = cms.InputTag("reducedEgamma","reducedEERecHits"),
    dataFormat = cms.int32(0), #0 = auto detection, 1 = AOD, 2 = miniAOD
    trkIsoConfig = trkIsol03CfgV2,
    trkIso04Config = trkIsol04CfgV2,
    makeTrkIso04 = cms.bool(True),
    posCalcLog = cms.PSet( T0_barl      = cms.double(7.4),
                           T0_endc      = cms.double(3.1),
                           T0_endcPresh = cms.double(1.2),
                           LogWeighted  = cms.bool(True),
                           W0           = cms.double(4.2),
                           X0           = cms.double(0.89) )
)
