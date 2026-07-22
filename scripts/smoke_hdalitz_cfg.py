"""Minimal smoke test of the ported HDalitzEle merged-electron XGBoost ID (15_0).
Runs HDalitzMergedIDProducer on slimmedElectrons and writes the ID branches to an
Electron NanoAOD table. No EventSetup needed. Input: the locally-generated UL2018 Z->ee MC."""
import FWCore.ParameterSet.Config as cms

process = cms.Process("HDALITZ")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 10
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(20))
process.source = cms.Source("PoolSource",
    fileNames=cms.untracked.vstring("file:/mnt/vdb/Codes/cmssw_dalitz/gen/miniaod.root"))
process.options = cms.untracked.PSet(numberOfThreads=cms.untracked.uint32(1))

process.load("HDalitzEle.MergedID.hdalitzMergedID_cfi")   # -> process.hdalitzMergedID

from PhysicsTools.NanoAOD.common_cff import Var, ExtVar
_ELE = cms.InputTag("slimmedElectrons")
_H = "hdalitzMergedID"
process.electronTable = cms.EDProducer("SimpleCandidateFlatTableProducer",
    src=_ELE, cut=cms.string(""), name=cms.string("Electron"),
    doc=cms.string("slimmedElectrons"), singleton=cms.bool(False), extension=cms.bool(False),
    variables=cms.PSet(
        pt=Var("pt", float, doc="pt", precision=10),
        eta=Var("eta", float, doc="eta", precision=12),
    ),
    externalVariables=cms.PSet(
        mvaHDalitzMergedID=ExtVar(cms.InputTag(_H, "hdalitzMergedIDScore"), float,
                                  doc="HDalitzEle merged-electron XGBoost signal-class score", precision=14),
        hdalitzMergedNGsf=ExtVar(cms.InputTag(_H, "hdalitzMergedNGsf"), int, doc="n associated GSF tracks"),
        hdalitzMergedCategory=ExtVar(cms.InputTag(_H, "hdalitzMergedCategory"), int,
                                     doc="0 M1EB, 1 M1EE, 2 M2EB, 3 M2EE"),
        hdalitzMergedWPTight=ExtVar(cms.InputTag(_H, "hdalitzMergedWPTight"), int, doc="pass tight WP"),
    ),
)

process.p = cms.Path(process.hdalitzMergedID + process.electronTable)
process.out = cms.OutputModule("NanoAODOutputModule",
    fileName=cms.untracked.string("file:nanoHDalitz.root"),
    outputCommands=cms.untracked.vstring("drop *", "keep nanoaodFlatTable_*_*_*"))
process.e = cms.EndPath(process.out)
