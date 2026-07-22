import FWCore.ParameterSet.Config as cms

process = cms.Process('MergedAnalyzer')

process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring('file:MiniAOD.root'),
    secondaryFileNames = cms.untracked.vstring()
)

process.options = cms.untracked.PSet()

process.TFileService = cms.Service("TFileService",
    fileName = cms.string('Ntuple.root')
)

process.load("Configuration.Geometry.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff")
process.GlobalTag.globaltag = cms.string("106X_mcRun2_asymptotic_v13")

process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
process.load("RecoLocalCalo.EcalRecAlgos.EcalSeverityLevelESProducer_cfi")
process.load("ZprimeTo4l.ModifiedHEEP.ModifiedHEEPIdVarValueMapProducer_cfi")
process.load("ZprimeTo4l.ModifiedHEEP.ModifiedEcalRecHitIsolationScone_cfi")
process.load("ZprimeTo4l.MergedLepton.MergedLeptonAnalyzer_cfi")

from PhysicsTools.PatUtils.l1PrefiringWeightProducer_cfi import l1PrefiringWeightProducer
process.prefiringweight = l1PrefiringWeightProducer.clone(
    TheJets = cms.InputTag("slimmedJets"), #this should be the slimmedJets collection with up to date JECs !
    DataEraECAL = cms.string("UL2016postVFP"),
    DataEraMuon = cms.string("2016postVFP"),
    UseJetEMPt = cms.bool(False),
    PrefiringRateSystematicUnctyECAL = cms.double(0.2),
    PrefiringRateSystematicUnctyMuon = cms.double(0.2)
)

process.mergedAnalyzer_step = cms.Path(
    process.prefiringweight*
    process.ModifiedHEEPIDVarValueMaps*
    process.ModifiedEcalRecHitIsolationScone*
    process.mergedLeptonAnalyzer
)

process.endjob_step = cms.EndPath(process.endOfProcess)

process.schedule = cms.Schedule(process.mergedAnalyzer_step,process.endjob_step)

# Automatic addition of the customisation function from Configuration.DataProcessing.Utils
from Configuration.DataProcessing.Utils import addMonitoring

#call to customisation function addMonitoring imported from Configuration.DataProcessing.Utils
process = addMonitoring(process)

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion
