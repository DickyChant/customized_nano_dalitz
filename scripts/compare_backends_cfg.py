"""Run BOTH inference backends (xgboost c-API and ONNXRuntime) on the same electrons in one
15_0 job and expose both scores, to prove they agree per-electron."""
import FWCore.ParameterSet.Config as cms

process = cms.Process("CMP")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 10
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(20))
process.source = cms.Source("PoolSource",
    fileNames=cms.untracked.vstring("file:/mnt/vdb/Codes/cmssw_dalitz/gen/miniaod.root"))
process.options = cms.untracked.PSet(numberOfThreads=cms.untracked.uint32(1))

from HDalitzEle.MergedID.hdalitzMergedID_cfi import hdalitzMergedID

def _m(ext):
    return dict(modelM1EB=cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M1EB.%s" % ext),
                modelM1EE=cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M1EE.%s" % ext),
                modelM2EB=cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M2EB.%s" % ext),
                modelM2EE=cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M2EE.%s" % ext))

process.hdalitzXgb  = hdalitzMergedID.clone(backend="xgboost", **_m("json"))
process.hdalitzOnnx = hdalitzMergedID.clone(backend="onnx",    **_m("onnx"))

from PhysicsTools.NanoAOD.common_cff import Var, ExtVar
process.electronTable = cms.EDProducer("SimpleCandidateFlatTableProducer",
    src=cms.InputTag("slimmedElectrons"), cut=cms.string(""), name=cms.string("Electron"),
    doc=cms.string("cmp"), singleton=cms.bool(False), extension=cms.bool(False),
    variables=cms.PSet(pt=Var("pt", float, doc="pt", precision=12),
                       eta=Var("eta", float, doc="eta", precision=14)),
    externalVariables=cms.PSet(
        mvaXgb =ExtVar(cms.InputTag("hdalitzXgb", "hdalitzMergedIDScore"),  float, doc="xgboost", precision=23),
        mvaOnnx=ExtVar(cms.InputTag("hdalitzOnnx","hdalitzMergedIDScore"),  float, doc="onnx",    precision=23),
        nGsf   =ExtVar(cms.InputTag("hdalitzXgb", "hdalitzMergedNGsf"),     int,   doc="nGsf"),
        catXgb =ExtVar(cms.InputTag("hdalitzXgb", "hdalitzMergedCategory"), int,   doc="cat"),
    ),
)
process.p = cms.Path(process.hdalitzXgb + process.hdalitzOnnx + process.electronTable)
process.out = cms.OutputModule("NanoAODOutputModule",
    fileName=cms.untracked.string("file:cmpBackends.root"),
    outputCommands=cms.untracked.vstring("drop *", "keep nanoaodFlatTable_*_*_*"))
process.e = cms.EndPath(process.out)
