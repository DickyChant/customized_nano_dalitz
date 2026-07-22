import FWCore.ParameterSet.Config as cms

process = cms.Process('mergedLeptonIDConversionAnalyzer')

process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(
      'file:MiniAOD.root'
    ),
    secondaryFileNames = cms.untracked.vstring()
)

process.options = cms.untracked.PSet( wantSummary = cms.untracked.bool(True) )

process.TFileService = cms.Service("TFileService",
    fileName = cms.string('hists.root')
)

process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.load("Configuration.Geometry.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff")
process.GlobalTag.globaltag = cms.string("106X_upgrade2018_realistic_v16_L1v1")

process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
process.load("RecoLocalCalo.EcalRecAlgos.EcalSeverityLevelESProducer_cfi")
process.load("ZprimeTo4l.ModifiedHEEP.ModifiedHEEPIdVarValueMapProducer_cfi")
process.load("ZprimeTo4l.ModifiedHEEP.ModifiedEcalRecHitIsolationScone_cfi")
process.load("ZprimeTo4l.MergedLepton.MergedLeptonIDProducer_cfi")
process.load("ZprimeTo4l.MergedLepton.MergedLeptonIDConversionAnalyzer_cfi")

runVIDmodules = [
    'RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_Fall17_94X_V2_cff',
    'RecoEgamma.ElectronIdentification.Identification.heepElectronID_HEEPV70_cff',
    'ZprimeTo4l.ModifiedHEEP.Identification.modifiedHeepElectronID_cff',
    'ZprimeTo4l.MergedLepton.Identification.mergedElectronID_20UL18_cff'
]

from RecoEgamma.EgammaTools.EgammaPostRecoTools import setupEgammaPostRecoSeq
setupEgammaPostRecoSeq(process,
                       runEnergyCorrections=False,
                       runVID=True,
                       eleIDModules=runVIDmodules,
                       phoIDModules=[],
                       era='2018-UL')

process.modifiedHEEPIDVarValueMaps2nd = process.ModifiedHEEPIDVarValueMaps.clone(
    elesMiniAOD=cms.InputTag("slimmedElectrons")
)

process.evtCounter = cms.EDAnalyzer('SimpleEventCounter')
process.evtCounter.isMC = cms.bool(True)

from HLTrigger.HLTfilters.hltHighLevel_cfi import hltHighLevel
process.hltFilter = hltHighLevel.clone()
process.hltFilter.throw = cms.bool(True)
process.hltFilter.HLTPaths = cms.vstring("HLT_IsoMu24_v*") # HLT_Mu9_IP6_part* HLT_IsoMu24_v*
process.hltFilter.TriggerResultsTag = cms.InputTag("TriggerResults","","HLT")

from PhysicsTools.PatUtils.l1PrefiringWeightProducer_cfi import l1PrefiringWeightProducer
process.prefiringweight = l1PrefiringWeightProducer.clone(
    TheJets = cms.InputTag("slimmedJets",processName=cms.InputTag.skipCurrentProcess()), #this should be the slimmedJets collection with up to date JECs
    TheMuons = cms.InputTag('slimmedMuons',processName=cms.InputTag.skipCurrentProcess()),
    ThePhotons = cms.InputTag('slimmedPhotons',processName=cms.InputTag.skipCurrentProcess()),
    DataEraECAL = cms.string("None"), #Use 2016BtoH for 2016
    DataEraMuon = cms.string("20172018"), #Use 2016 for 2016
    UseJetEMPt = cms.bool(False),
    PrefiringRateSystematicUnctyECAL = cms.double(0.2),
    PrefiringRateSystematicUnctyMuon = cms.double(0.2)
)

process.mergedLeptonIDConversionAnalyzer.isMC = cms.bool(True)

process.p = cms.Path(
    process.evtCounter+
    process.hltFilter+
    process.prefiringweight+
    process.ModifiedHEEPIDVarValueMaps+
    process.ModifiedEcalRecHitIsolationScone+
    process.mergedLeptonIDProducer20UL18+
    process.egammaPostRecoSeq+
    process.modifiedHEEPIDVarValueMaps2nd+
    process.mergedLeptonIDConversionAnalyzer
)

# Automatic addition of the customisation function from Configuration.DataProcessing.Utils
from Configuration.DataProcessing.Utils import addMonitoring

#call to customisation function addMonitoring imported from Configuration.DataProcessing.Utils
process = addMonitoring(process)

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion
