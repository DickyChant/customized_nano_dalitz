import FWCore.ParameterSet.Config as cms

# chw1207/HDalitzEle merged-electron XGBoost ID as electron ValueMaps.
hdalitzMergedID = cms.EDProducer("HDalitzMergedIDProducer",
    srcEle       = cms.InputTag("slimmedElectrons"),
    srcGsfTracks = cms.InputTag("reducedEgamma", "reducedGsfTracks"),
    srcRho       = cms.InputTag("fixedGridRhoFastjetAll"),
    srcVertices  = cms.InputTag("offlineSlimmedPrimaryVertices"),
    backend      = cms.string("onnx"),   # "onnx" (portable) or "xgboost" (15_0 only)
    modelM1EB = cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M1EB.onnx"),
    modelM1EE = cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M1EE.onnx"),
    modelM2EB = cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M2EB.onnx"),
    modelM2EE = cms.FileInPath("HDalitzEle/MergedID/data/HDalitzMergedID_M2EE.onnx"),
    m1EBWPTight = cms.double(0.4390),
    m1EEWPTight = cms.double(0.4381),
    m2EBWPTight = cms.double(0.808),
    m2EEWPTight = cms.double(0.723),
)
