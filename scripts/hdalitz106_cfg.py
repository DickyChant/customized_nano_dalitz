"""HDalitzEle merged-electron ID via ONNXRuntime in CMSSW_10_6_X, on the same UL2018 Z->ee MC."""
import FWCore.ParameterSet.Config as cms

process = cms.Process("HDAL106")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 10
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(20))
process.source = cms.Source("PoolSource",
    fileNames=cms.untracked.vstring("file:/mnt/vdb/Codes/cmssw_dalitz/gen/miniaod.root"))
process.options = cms.untracked.PSet(numberOfThreads=cms.untracked.uint32(1))

process.load("HDalitzEle.MergedID.hdalitzMergedID_cfi")   # backend defaults to "onnx"

from PhysicsTools.NanoAOD.common_cff import Var, ExtVar
_H = "hdalitzMergedID"
process.electronTable = cms.EDProducer("SimpleCandidateFlatTableProducer",
    src=cms.InputTag("slimmedElectrons"), cut=cms.string(""), name=cms.string("Electron"),
    doc=cms.string("hdal106"), singleton=cms.bool(False), extension=cms.bool(False),
    variables=cms.PSet(pt=Var("pt", float, doc="pt", precision=12),
                       eta=Var("eta", float, doc="eta", precision=14)),
    externalVariables=cms.PSet(
        mvaOnnx106=ExtVar(cms.InputTag(_H, "hdalitzMergedIDScore"), float, doc="onnx 10_6", precision=23),
        nGsf     =ExtVar(cms.InputTag(_H, "hdalitzMergedNGsf"),     int, doc="nGsf"),
        cat      =ExtVar(cms.InputTag(_H, "hdalitzMergedCategory"), int, doc="cat"),
    ),
)
process.p = cms.Path(process.hdalitzMergedID + process.electronTable)
process.out = cms.OutputModule("NanoAODOutputModule",
    fileName=cms.untracked.string("file:nanoHDalitz106.root"),
    outputCommands=cms.untracked.vstring("drop *", "keep nanoaodFlatTable_*_*_*"))
process.e = cms.EndPath(process.out)
