import FWCore.ParameterSet.Config as cms

mergedEleSigAnalyzer = cms.EDAnalyzer("MergedEleSigAnalyzer",
  srcEle=cms.InputTag("slimmedElectrons"),
  srcGenPtc=cms.InputTag("prunedGenParticles"),
  srcPv=cms.InputTag("offlineSlimmedPrimaryVertices"),
  addGsfTrkMap = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","eleAddGsfTrk"),
  addPackedCandMap = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","eleAddPackedCand"),
  dPerpIn = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","dPerpIn"),
  union5x5dEtaIn = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","union5x5dEtaIn"),
  union5x5Energy = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","union5x5Energy"),
  generator = cms.InputTag("generator"),
  ptThres = cms.double(20.),
  ptThres2nd = cms.double(10.),
  drThres = cms.double(0.001)
)
