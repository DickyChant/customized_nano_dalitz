import FWCore.ParameterSet.Config as cms

mergedLeptonIDProducer = cms.EDProducer("MergedLeptonIDProducer", # 20UL16
  srcEle=cms.InputTag("slimmedElectrons",processName=cms.InputTag.skipCurrentProcess()),
  addGsfTrkMap = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddGsfTrk"),
  addPackedCandMap = cms.InputTag("ModifiedHEEPIDVarValueMaps","eleAddPackedCand"),
  dPerpIn = cms.InputTag("ModifiedHEEPIDVarValueMaps","dPerpIn"),
  dEtaInSeed2nd = cms.InputTag("ModifiedHEEPIDVarValueMaps","dEtaInSeed2nd"),
  dPhiInSC2nd = cms.InputTag("ModifiedHEEPIDVarValueMaps","dPhiInSC2nd"),
  alphaTrack = cms.InputTag("ModifiedHEEPIDVarValueMaps","alphaTrack"),
  alphaCalo = cms.InputTag("ModifiedHEEPIDVarValueMaps","alphaCalo"),
  normalizedDParaIn = cms.InputTag("ModifiedHEEPIDVarValueMaps","normalizedDParaIn"),
  union5x5covIeIe = cms.InputTag("ModifiedHEEPIDVarValueMaps","union5x5covIeIe"),
  union5x5covIeIp = cms.InputTag("ModifiedHEEPIDVarValueMaps","union5x5covIeIp"),
  union5x5covIpIp = cms.InputTag("ModifiedHEEPIDVarValueMaps","union5x5covIpIp"),
  union5x5dEtaIn = cms.InputTag("ModifiedHEEPIDVarValueMaps","union5x5dEtaIn"),
  union5x5dPhiIn = cms.InputTag("ModifiedHEEPIDVarValueMaps","union5x5dPhiIn"),
  xgbPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL16.xml"),
  meanstdPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL16.csv"),
  xgbPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL16.xml"),
  meanstdPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL16.csv")
)

mergedLeptonIDProducer20UL16APV = mergedLeptonIDProducer.clone(
  xgbPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL16APV.xml"),
  meanstdPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL16APV.csv"),
  xgbPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL16APV.xml"),
  meanstdPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL16APV.csv")
)

mergedLeptonIDProducer20UL17 = mergedLeptonIDProducer.clone(
  xgbPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL17.xml"),
  meanstdPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL17.csv"),
  xgbPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL17.xml"),
  meanstdPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL17.csv")
)

mergedLeptonIDProducer20UL18 = mergedLeptonIDProducer.clone(
  xgbPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL18.xml"),
  meanstdPathHasTrkEB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/HasTrk_EB_20UL18.csv"),
  xgbPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL18.xml"),
  meanstdPathNoneEt2EB=cms.FileInPath("ZprimeTo4l/MergedLepton/data/NoneEt2_EB_20UL18.csv")
)
