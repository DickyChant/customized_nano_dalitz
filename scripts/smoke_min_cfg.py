"""Minimal electron-only smoke test of the ported merged-electron ID on real Run2 data.
Runs ModifiedHEEPIDVarValueMaps + mergedLeptonIDProducer on slimmedElectrons and writes a
NanoAOD Electron table carrying the two merged-ID branches. Avoids the full nano jet/MET
cross-linking machinery (the di-electron skim used as input is stripped of those)."""
import FWCore.ParameterSet.Config as cms

INFILE = 'file:/mnt/vdb/Codes/cmssw_dalitz/gen/miniaod.root'   # locally-generated UL2018 Z->ee MC
ELE = cms.InputTag("slimmedElectrons")                        # single product in generated MINIAOD

process = cms.Process("NANODALITZ")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.Geometry.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, "106X_upgrade2018_realistic_v16", "")
process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
process.load("RecoLocalCalo.EcalRecAlgos.EcalSeverityLevelESProducer_cfi")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 50

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(300))
process.source = cms.Source("PoolSource", fileNames=cms.untracked.vstring(INFILE))

# 1) ModifiedHEEP value maps (on slimmedElectrons)
from ZprimeTo4l.ModifiedHEEP.ModifiedHEEPIdVarValueMapProducer_cfi import ModifiedHEEPIDVarValueMaps
process.mergedHEEPIDVarValueMaps = ModifiedHEEPIDVarValueMaps.clone(
    elesMiniAOD=ELE, dataFormat=cms.int32(2))

# 2) merged-electron MVA (UL17 models)
from ZprimeTo4l.MergedLepton.MergedLeptonIDProducer_cfi import mergedLeptonIDProducer20UL18
_H = "mergedHEEPIDVarValueMaps"
process.mergedLeptonIDProducer = mergedLeptonIDProducer20UL18.clone(
    srcEle=ELE,
    addGsfTrkMap=cms.InputTag(_H, "eleAddGsfTrk"),
    addPackedCandMap=cms.InputTag(_H, "eleAddPackedCand"),
    dPerpIn=cms.InputTag(_H, "dPerpIn"),
    dEtaInSeed2nd=cms.InputTag(_H, "dEtaInSeed2nd"),
    dPhiInSC2nd=cms.InputTag(_H, "dPhiInSC2nd"),
    alphaTrack=cms.InputTag(_H, "alphaTrack"),
    alphaCalo=cms.InputTag(_H, "alphaCalo"),
    normalizedDParaIn=cms.InputTag(_H, "normalizedDParaIn"),
    union5x5covIeIe=cms.InputTag(_H, "union5x5covIeIe"),
    union5x5covIeIp=cms.InputTag(_H, "union5x5covIeIp"),
    union5x5covIpIp=cms.InputTag(_H, "union5x5covIpIp"),
    union5x5dEtaIn=cms.InputTag(_H, "union5x5dEtaIn"),
    union5x5dPhiIn=cms.InputTag(_H, "union5x5dPhiIn"),
)

# 3) Electron flat table on slimmedElectrons + the two merged-ID external variables
from PhysicsTools.NanoAOD.common_cff import Var, ExtVar
process.electronTable = cms.EDProducer("SimpleCandidateFlatTableProducer",
    src=ELE, cut=cms.string(""), name=cms.string("Electron"),
    doc=cms.string("slimmedElectrons"), singleton=cms.bool(False), extension=cms.bool(False),
    variables=cms.PSet(
        pt=Var("pt", float, doc="pt", precision=10),
        eta=Var("eta", float, doc="eta", precision=12),
        phi=Var("phi", float, doc="phi", precision=10),
        charge=Var("charge", int, doc="charge"),
    ),
    externalVariables=cms.PSet(
        mvaMergedElectron=ExtVar(cms.InputTag("mergedLeptonIDProducer", "mvaMergedElectronValues"),
                                 float, doc="merged-electron MVA (EB only; -1 N/A)", precision=14),
        mvaMergedElectronCategory=ExtVar(cms.InputTag("mergedLeptonIDProducer", "mvaMergedElectronCategories"),
                                         int, doc="merged-electron MVA category (-1/0/1)"),
    ),
)

process.p = cms.Path(process.mergedHEEPIDVarValueMaps
                     + process.mergedLeptonIDProducer
                     + process.electronTable)
process.out = cms.OutputModule("NanoAODOutputModule",
    fileName=cms.untracked.string("file:nanoDalitzMin.root"),
    outputCommands=cms.untracked.vstring("drop *", "keep nanoaodFlatTable_*_*_*"))
process.e = cms.EndPath(process.out)
