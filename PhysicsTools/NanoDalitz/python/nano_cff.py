"""Customized-NanoAOD glue: port the ZprimeTo4l merged-electron ID into two extra
Electron branches.

Usage (cmsDriver):
  --customise PhysicsTools/NanoDalitz/nano_cff.customizeMergedElectron

The merged-electron MVA (barrel-only) is exposed as:
  Electron_mvaMergedElectron          (float) sigmoid score; -1 sentinel where N/A
  Electron_mvaMergedElectronCategory  (int)   -1 Null, 0 HasTrk, 1 NoTrkEt2

Design note: the producer chain runs on `linkedObjects:electrons` (the exact collection
the nano electronTable iterates), mirroring electronMVATTH, so the ValueMap keys match the
table src and ExtVar resolves without any ref-chain gymnastics.
"""
import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import ExtVar

# per-UL-year MergedLeptonIDProducer clones (defined in the upstream _cfi)
_MERGED_BY_YEAR = {
    "2016APV": "mergedLeptonIDProducer20UL16APV",
    "2016":    "mergedLeptonIDProducer",       # 20UL16 default clone
    "2017":    "mergedLeptonIDProducer20UL17",
    "2018":    "mergedLeptonIDProducer20UL18",
}

_ELE_SRC = cms.InputTag("linkedObjects", "electrons")


def customizeMergedElectron(process, year="2018"):
    # --- EventSetup the producers need but a bare NANO job does not load ---
    process.load("Configuration.StandardSequences.MagneticField_cff")
    process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
    process.load("RecoLocalCalo.EcalRecAlgos.EcalSeverityLevelESProducer_cfi")

    # --- ModifiedHEEP value-map producer (run on the final nano electron collection) ---
    from ZprimeTo4l.ModifiedHEEP.ModifiedHEEPIdVarValueMapProducer_cfi import ModifiedHEEPIDVarValueMaps
    heep = ModifiedHEEPIDVarValueMaps.clone(
        elesMiniAOD=_ELE_SRC,
        dataFormat=cms.int32(2),   # force miniAOD path
    )
    process.mergedHEEPIDVarValueMaps = heep

    # --- MergedLepton ID producer (consumes the HEEP value maps + the same electrons) ---
    import ZprimeTo4l.MergedLepton.MergedLeptonIDProducer_cfi as _mcfi
    if year not in _MERGED_BY_YEAR:
        raise ValueError("customizeMergedElectron: unknown year %r (choose from %s)"
                         % (year, list(_MERGED_BY_YEAR)))
    merged = getattr(_mcfi, _MERGED_BY_YEAR[year]).clone(
        srcEle=_ELE_SRC,
        addGsfTrkMap=cms.InputTag("mergedHEEPIDVarValueMaps", "eleAddGsfTrk"),
        addPackedCandMap=cms.InputTag("mergedHEEPIDVarValueMaps", "eleAddPackedCand"),
        dPerpIn=cms.InputTag("mergedHEEPIDVarValueMaps", "dPerpIn"),
        dEtaInSeed2nd=cms.InputTag("mergedHEEPIDVarValueMaps", "dEtaInSeed2nd"),
        dPhiInSC2nd=cms.InputTag("mergedHEEPIDVarValueMaps", "dPhiInSC2nd"),
        alphaTrack=cms.InputTag("mergedHEEPIDVarValueMaps", "alphaTrack"),
        alphaCalo=cms.InputTag("mergedHEEPIDVarValueMaps", "alphaCalo"),
        normalizedDParaIn=cms.InputTag("mergedHEEPIDVarValueMaps", "normalizedDParaIn"),
        union5x5covIeIe=cms.InputTag("mergedHEEPIDVarValueMaps", "union5x5covIeIe"),
        union5x5covIeIp=cms.InputTag("mergedHEEPIDVarValueMaps", "union5x5covIeIp"),
        union5x5covIpIp=cms.InputTag("mergedHEEPIDVarValueMaps", "union5x5covIpIp"),
        union5x5dEtaIn=cms.InputTag("mergedHEEPIDVarValueMaps", "union5x5dEtaIn"),
        union5x5dPhiIn=cms.InputTag("mergedHEEPIDVarValueMaps", "union5x5dPhiIn"),
    )
    process.mergedLeptonIDProducer = merged

    # --- expose as external variables on the standard Electron table ---
    process.electronTable.externalVariables.mvaMergedElectron = ExtVar(
        cms.InputTag("mergedLeptonIDProducer", "mvaMergedElectronValues"), float,
        doc="ZprimeTo4l merged-electron MVA score (EB only; -1 if N/A)", precision=14)
    process.electronTable.externalVariables.mvaMergedElectronCategory = ExtVar(
        cms.InputTag("mergedLeptonIDProducer", "mvaMergedElectronCategories"), int,
        doc="merged-electron MVA category: -1 Null, 0 HasTrk, 1 NoTrkEt2")

    # --- schedule the two producers (unscheduled Task; ExtVar wiring fixes ordering) ---
    process.mergedElectronIDTask = cms.Task(process.mergedHEEPIDVarValueMaps,
                                            process.mergedLeptonIDProducer)
    if hasattr(process, "schedule") and process.schedule is not None:
        process.schedule.associate(process.mergedElectronIDTask)
    else:
        for p in process.paths_().values():
            p.associate(process.mergedElectronIDTask)

    return process


def dropMET(process):
    """Remove MET-dependent nano modules (needed when the input MINIAOD skim lacks
    slimmedMETs, e.g. the egamma di-electron skims). Irrelevant to the electron-ID port."""
    victims = set(n for n in list(process.producers_()) + list(process.filters_())
                  if "met" in n.lower())
    for coll in list(process.paths_().values()) + list(process.endpaths_().values()) \
              + list(process.tasks_().values()):
        for v in victims:
            if hasattr(process, v):
                coll.remove(getattr(process, v))
    print("[NanoDalitz] dropMET removed:", sorted(victims))
    return process


def dropTrigger(process):
    """Remove PAT/nano trigger-unpacking modules (for locally-generated MC produced without
    an HLT step, so TriggerResults::HLT does not exist)."""
    victims = set(n for n in list(process.producers_()) + list(process.filters_())
                  if "rigger" in n.lower())
    for coll in list(process.paths_().values()) + list(process.endpaths_().values()) \
              + list(process.tasks_().values()):
        for v in victims:
            if hasattr(process, v):
                coll.remove(getattr(process, v))
    print("[NanoDalitz] dropTrigger removed:", sorted(victims))
    return process


def customizeMergedElectron2017NoMET(process):
    process = customizeMergedElectron(process, "2017")
    return dropMET(process)


# convenience per-year entry points (cmsDriver --customise takes a single dotted name)
def customizeMergedElectron2016APV(process):
    return customizeMergedElectron(process, "2016APV")


def customizeMergedElectron2016(process):
    return customizeMergedElectron(process, "2016")


def customizeMergedElectron2017(process):
    return customizeMergedElectron(process, "2017")


def customizeMergedElectron2018(process):
    return customizeMergedElectron(process, "2018")


# ---------------------------------------------------------------------------
# HDalitzEle (chw1207) merged-electron XGBoost ID -- portable (10_6 + 15_0)
# backend via the cfi 'backend' param: onnx (default, both releases) or xgboost (15_0).
# Adds branches ALONGSIDE the ZprimeTo4l merged ID.
# ---------------------------------------------------------------------------
def customizeHDalitzMergedElectron(process):
    from PhysicsTools.NanoAOD.common_cff import ExtVar
    from HDalitzEle.MergedID.hdalitzMergedID_cfi import hdalitzMergedID
    ele = cms.InputTag("linkedObjects", "electrons")   # the collection electronTable iterates
    process.hdalitzMergedID = hdalitzMergedID.clone(srcEle=ele)

    ev = process.electronTable.externalVariables
    ev.mvaHDalitzMergedID = ExtVar(cms.InputTag("hdalitzMergedID", "hdalitzMergedIDScore"), float,
                                   doc="HDalitzEle merged-electron ID score (Merged-1Gsf/2Gsf, XGBoost via onnx/xgb backend)", precision=14)
    ev.hdalitzMergedNGsf = ExtVar(cms.InputTag("hdalitzMergedID", "hdalitzMergedNGsf"), "int",
                                  doc="HDalitzEle: n associated GSF tracks")
    ev.hdalitzMergedCategory = ExtVar(cms.InputTag("hdalitzMergedID", "hdalitzMergedCategory"), "int",
                                      doc="HDalitzEle merged-ID category: 0 M1EB, 1 M1EE, 2 M2EB, 3 M2EE")
    ev.hdalitzMergedWPTight = ExtVar(cms.InputTag("hdalitzMergedID", "hdalitzMergedWPTight"), "int",
                                     doc="HDalitzEle merged-ID passes tight WP")

    task = cms.Task(process.hdalitzMergedID)
    process.hdalitzMergedIDTask = task
    if hasattr(process, "schedule") and process.schedule is not None:
        process.schedule.associate(task)
    else:
        for p in process.paths_().values():
            p.associate(task)
    return process


def customizeAllMergedElectron(process, year="2018"):
    """Both merged-electron IDs at once: ZprimeTo4l (GBRForest) + HDalitzEle (XGBoost)."""
    process = customizeMergedElectron(process, year)
    return customizeHDalitzMergedElectron(process)
