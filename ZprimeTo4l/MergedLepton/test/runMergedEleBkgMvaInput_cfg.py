import FWCore.ParameterSet.Config as cms

process = cms.Process('mergedEleBkgMvaInput')

process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')

process.MessageLogger.cerr.FwkReport.reportEvery = 1000

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
process.GlobalTag.globaltag = cms.string("106X_mcRun2_asymptotic_v17")

process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
process.load("RecoLocalCalo.EcalRecAlgos.EcalSeverityLevelESProducer_cfi")
process.load("ZprimeTo4l.ModifiedHEEP.ModifiedHEEPIdVarValueMapProducer_cfi")
process.load("ZprimeTo4l.ModifiedHEEP.ModifiedEcalRecHitIsolationScone_cfi")
process.load("ZprimeTo4l.MergedLepton.MergedEleBkgMvaInput_cfi")

runVIDmodules = [
    'ZprimeTo4l.ModifiedHEEP.Identification.modifiedHeepElectronID_cff',
]

from RecoEgamma.EgammaTools.EgammaPostRecoTools import setupEgammaPostRecoSeq
setupEgammaPostRecoSeq(process,
                       runEnergyCorrections=False,
                       runVID=True,
                       eleIDModules=runVIDmodules,
                       phoIDModules=[],
                       era='2016postVFP-UL')

process.modifiedHEEPIDVarValueMaps2nd = process.ModifiedHEEPIDVarValueMaps.clone(
    elesMiniAOD=cms.InputTag("slimmedElectrons")
)

process.modifiedEcalRecHitIsolationScone2nd = process.ModifiedEcalRecHitIsolationScone.clone(
    emObjectProducer=cms.InputTag("slimmedElectrons"),
    addGsfTrkMap = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","eleAddGsfTrk"),
    addPackedCandMap = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","eleAddPackedCand"),
    dEtaInSeed2nd = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","dEtaInSeed2nd"),
    dPhiInSC2nd = cms.InputTag("modifiedHEEPIDVarValueMaps2nd","dPhiInSC2nd")
)

process.analyzer_step = cms.Path(
    process.ModifiedHEEPIDVarValueMaps*
    process.ModifiedEcalRecHitIsolationScone*
    process.egammaPostRecoSeq*
    process.modifiedHEEPIDVarValueMaps2nd*
    process.modifiedEcalRecHitIsolationScone2nd*
    process.mergedEleBkgMvaInput
)

process.endjob_step = cms.EndPath(process.endOfProcess)

process.schedule = cms.Schedule(process.analyzer_step,process.endjob_step)

# Automatic addition of the customisation function from Configuration.DataProcessing.Utils
from Configuration.DataProcessing.Utils import addMonitoring

#call to customisation function addMonitoring imported from Configuration.DataProcessing.Utils
process = addMonitoring(process)

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion
