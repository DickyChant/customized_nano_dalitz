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

    # --- PF-based additional leg -------------------------------------------------
    # A merged electron's second leg is either a 2nd GSF track or a packed PF candidate, and
    # ~85% of electrons have NO 2nd GSF track -- so for most of them this is the only handle
    # on the second leg. It also carries lostInnerHits(), the conversion discriminator that
    # actually works in MiniAOD (a ref-based per-GSF-track conversion veto is impossible:
    # MiniAOD conversions are built from general tracks whose Refs are dropped).
    process.mergedEleAddPackedCand = cms.EDProducer(
        "MergedEleAddPackedCandTableProducer",
        srcEle=_ELE_SRC,
        addPackedCandMap=cms.InputTag("mergedHEEPIDVarValueMaps", "eleAddPackedCand"),
    )
    _pc = {
        "addPackedCandPt":  ("pfAddCandPt",  float, "pt of the PF candidate forming the 2nd leg"),
        "addPackedCandEta": ("pfAddCandEta", float, "eta of the PF 2nd leg"),
        "addPackedCandPhi": ("pfAddCandPhi", float, "phi of the PF 2nd leg"),
        "addPackedCandDxy": ("pfAddCandDxy", float, "dxy of the PF 2nd leg"),
        "addPackedCandDz":  ("pfAddCandDz",  float, "dz of the PF 2nd leg"),
        "addPackedCandCharge":        ("pfAddCandCharge", "int", "charge of the PF 2nd leg"),
        "addPackedCandLostInnerHits": ("pfAddCandLostInnerHits", "int",
                                       "lost inner hits of the PF 2nd leg: -1 valid hit in first "
                                       "pixel layer (least conversion-like), 0 none, 1 one, 2 more "
                                       "-- the MiniAOD conversion discriminator for this leg"),
        "addPackedCandPixelHits":  ("pfAddCandPixelHits", "int", "pixel hits of the PF 2nd leg"),
        "addPackedCandNHits":      ("pfAddCandNHits", "int", "tracker hits of the PF 2nd leg"),
        "addPackedCandHighPurity": ("pfAddCandHighPurity", "int", "PF 2nd leg track is high purity"),
        "addPackedCandExists":     ("pfHasAddCand", "int", "a PF candidate 2nd leg was found"),
    }
    for label, spec in _pc.items():
        name, typ, doc = spec
        kw = dict(doc=doc)
        if typ is float:
            kw["precision"] = 14
        process.electronTable.externalVariables.__setattr__(
            name, ExtVar(cms.InputTag("mergedEleAddPackedCand", label), typ, **kw))

    # --- schedule the producers (unscheduled Task; ExtVar wiring fixes ordering) ---
    process.mergedElectronIDTask = cms.Task(process.mergedHEEPIDVarValueMaps,
                                            process.mergedLeptonIDProducer,
                                            process.mergedEleAddPackedCand)
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


# ---------------------------------------------------------------------------
# Output slimming for the H->ee-gamma merged-electron analysis.
# Drops nano tables with no role in the channel to shrink the output (data is ~92% of
# the total on-disk volume, so these cuts compound over the whole production).
# ---------------------------------------------------------------------------
# Only branch-writing table modules are removed -- their upstream producers (finalJets,
# the AK8 ParticleNet/DeepBoosted taggers, softActivityJets, ProtonProducer inputs, ...) are
# left in place but go unscheduled once nothing consumes them, so kept tables never break and
# the heavy taggers simply stop running.
#   KEEP (per request): Jet(AK4), Electron, Photon, Muon, Tau, CorrT1METJet,
#                       MET/PuppiMET/DeepMET, SV, PV, trigger, gen.
#   DROP: boostedTau, LowPtElectron, Proton/PPS, IsoTrack, SoftActivityJet, FatJet/SubJet/AK8(+gen/MC).
# Exact module names (the module name != the branch/collection name for several of these:
# SoftActivityJet -> saJetTable/saTable; Proton/PPSLocalTrack -> protonTable+multiRP/singleRP).
# The proton family MUST drop together: multiRP/singleRP tables read ExtVars from protonTable,
# so dropping protonTable alone would leave a dangling ref and crash data jobs.
_SLIM_DROP_EXACT = {
    "boostedTauTable", "boostedTauMCTable",                                         # boostedTau
    "lowPtElectronTable", "lowPtElectronMCTable", "lowPtElectronsMCMatchForTable",  # LowPtElectron
    "isoTrackTable",                                                                # IsoTrack
    "saJetTable", "saTable",                                                        # SoftActivity(Jet)
    "protonTable", "multiRPTable", "singleRPTable", "genProtonTable",               # Proton / PPS
}
# FatJet/SubJet/AK8 spans many gen/MC/constituent tables -> match the whole family by substring.
_SLIM_DROP_SUBSTR = ("fatjet", "subjet", "ak8")


def slimNanoDalitz(process):
    victims = sorted(n for n in list(process.producers_())
                     if n in _SLIM_DROP_EXACT
                     or (n.endswith("Table") and any(s in n.lower() for s in _SLIM_DROP_SUBSTR)))
    for coll in list(process.paths_().values()) + list(process.endpaths_().values()) \
              + list(process.tasks_().values()):
        for v in victims:
            if hasattr(process, v):
                coll.remove(getattr(process, v))
    # boostedTau: removing its tables is not enough -- linkedObjects consumes finalBoostedTaus, which
    # drags in the anti-electron MVA6 discriminant (and, on 15_0-over-UL, a missing GBRForest ES).
    # The PATObjectCrossLinker guards every boostedTau use on a non-empty label, so detaching the
    # input here leaves the whole boostedTau producer chain unscheduled.
    if hasattr(process, "linkedObjects"):
        process.linkedObjects.boostedTaus = cms.InputTag("")
    print("[NanoDalitz] slimNanoDalitz dropped %d tables: %s (+ detached linkedObjects.boostedTaus)"
          % (len(victims), victims))
    return process


# NOTE on boostedTau + the _15X twins: running the Run2 (106Xv2-modifier) boostedTau nano
# table under a 15_0 release on UL MiniAOD is not viable -- the modifier adds the boostedTau
# 'againstEle' MVA6 discriminant and `linkedObjects` consumes `finalBoostedTaus`, so the
# discriminant runs unconditionally and asks the EventSetup for a GBRForest labelled
# 'RecoTauTag_antiElectronMVA_NoEleMatch_..._BL' that the UL conditions ship only under a
# different name (NoProductResolverException). boostedTau is therefore produced on the native
# 10_6 Run2 path (and on Run3), not on the _15X twins.  See docs / the crab README.


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
def _addMergedEleInputVars(process):
    """Electron-table variables the merged-electron ID consumes that stock NanoAOD omits.

    All are plain pat::Electron accessors, so they cost nothing but the branch. Stock nano
    already ships rho, superclusterEta, rawEnergy, hoe, eInvMinusPInv, sieie, r9, fbrem and
    energyErr; these are the remaining ID inputs, plus the split PF-isolation components
    (nano only stores the combined pfRelIso03_all / _chg) and the PF-cluster isolations
    (present for photons but not electrons). Names follow the CMSSW electron MVA-variable
    conventions where one exists.
    """
    from PhysicsTools.NanoAOD.common_cff import Var
    v = process.electronTable.variables
    v.dEtaSCTrkAtVtx = Var("deltaEtaSuperClusterTrackAtVtx", float, precision=14,
                           doc="dEta(SC seed, track) at vertex")
    v.dPhiSCTrkAtVtx = Var("deltaPhiSuperClusterTrackAtVtx", float, precision=14,
                           doc="dPhi(SC seed, track) at vertex")
    # Supercluster phi. Nano ships superclusterEta but NOT phi, and it is needed twice over:
    # it is an input feature of the merged-electron energy regression, and the analysis matches
    # an electron to a photon by exact SC (eta, phi) equality in the Hgg preselection.
    v.superclusterPhi = Var("superCluster().phi()", float, precision=14,
                            doc="supercluster phi")
    v.superclusterEnergy = Var("superCluster().energy()", float, precision=14,
                               doc="supercluster energy (corrected; cf. rawEnergy)")
    # preshower plane energies -- nano ships only the total (PreshowerEnergy). The EE energy
    # regression uses (ESEnP1+ESEnP2)/SCRawEn, which the total already gives, but the planes
    # are what ggNtuple stores so keep them separable.
    v.esEnergyPlane1 = Var("superCluster().preshowerEnergyPlane1()", float, precision=14,
                           doc="preshower energy, plane 1")
    v.esEnergyPlane2 = Var("superCluster().preshowerEnergyPlane2()", float, precision=14,
                           doc="preshower energy, plane 2")
    v.scEtaWidth = Var("superCluster().etaWidth()", float, precision=14, doc="supercluster eta width")
    v.scPhiWidth = Var("superCluster().phiWidth()", float, precision=14, doc="supercluster phi width")
    v.sipip = Var("full5x5_sigmaIphiIphi()", float, precision=14, doc="full5x5 sigma_iphiiphi")
    v.eSCOverP = Var("eSuperClusterOverP()", float, precision=14, doc="E(SC)/p at vertex")
    v.eEleOverPout = Var("eEleClusterOverPout()", float, precision=14,
                         doc="E(ele cluster)/p_out at the calorimeter")
    v.gsfTrkChi2 = Var("gsfTrack().normalizedChi2()", float, precision=14,
                       doc="normalized chi2 of the GSF track")
    v.pfChIso = Var("pfIsolationVariables().sumChargedHadronPt", float, precision=14,
                    doc="PF charged-hadron isolation (absolute, dR=0.3)")
    v.pfPhoIso = Var("pfIsolationVariables().sumPhotonEt", float, precision=14,
                     doc="PF photon isolation (absolute, dR=0.3)")
    v.pfNeuIso = Var("pfIsolationVariables().sumNeutralHadronEt", float, precision=14,
                     doc="PF neutral-hadron isolation (absolute, dR=0.3)")
    v.pfPUIso = Var("pfIsolationVariables().sumPUPt", float, precision=14,
                    doc="PF pileup isolation (absolute, dR=0.3)")
    v.ecalPFClusIso = Var("ecalPFClusterIso()", float, precision=14, doc="ECAL PF-cluster isolation")
    v.hcalPFClusIso = Var("hcalPFClusterIso()", float, precision=14, doc="HCAL PF-cluster isolation")
    # Photon side: the electron->photon match in the Hgg preselection compares SC (eta, phi)
    # on BOTH objects, so the photon needs phi too (nano ships only superclusterEta here as well).
    pho = getattr(process, "photonTable", None)
    if pho is not None:
        pho.variables.superclusterPhi = Var("superCluster().phi()", float, precision=14,
                                            doc="supercluster phi")
        pho.variables.superclusterEnergy = Var("superCluster().energy()", float, precision=14,
                                               doc="supercluster energy (corrected; cf. energyRaw)")
        # nano exposes the charged and photon components (pfChargedIso, pfPhoIso03) but not the
        # neutral-hadron one; the Hgg preselection uses all three separately.
        pho.variables.pfNeuIso = Var("neutralHadronIso()", float, precision=14,
                                     doc="PF absolute isolation dR=0.3, neutral-hadron component (uncorrected)")
        # preshower plane energies -- nano ships only the ES/raw ratio (esEnergyOverRawE)
        pho.variables.esEnergyPlane1 = Var("superCluster().preshowerEnergyPlane1()", float,
                                           precision=14, doc="preshower energy, plane 1")
        pho.variables.esEnergyPlane2 = Var("superCluster().preshowerEnergyPlane2()", float,
                                           precision=14, doc="preshower energy, plane 2")
    _addEgmScaleSmearVars(process)
    return process


# EGM energy scale & smearing. The UL MiniAODv2 slimmedElectrons/slimmedPhotons already carry
# these as userFloats (the EGM post-reco ran in the MiniAOD step), so no extra sequence is
# needed -- they only have to be written out.
#
# Two things to know before using them (both verified on UL18 signal MC):
#  1. Every variation is an ENERGY in GeV, not a pT. To vary pT, scale by
#     (variation / nominal), i.e.  pt_varied = pt * variation / <reference energy>.
#  2. The *reference* differs by collection: for ELECTRONS the variations are of the combined
#     ECAL+track energy `egmEnergyTrkPostCorr`, NOT the ECAL-only `egmEnergyPostCorr`
#     (checked: the scale variations reproduce ecalTrkEnergyPostCorr exactly). For PHOTONS
#     the reference is `egmEnergyPostCorr`.
# In MC the scale up/down variations are identical to each other by EGM convention -- the
# scale uncertainty is applied to data, while MC receives the resolution smearing instead.
_EGM_SYST = {
    "energyScaleStatUp":   ("egmScaleStatUp",   "energy scale, statistical  up   variation [GeV]"),
    "energyScaleStatDown": ("egmScaleStatDn",   "energy scale, statistical  down variation [GeV]"),
    "energyScaleSystUp":   ("egmScaleSystUp",   "energy scale, systematic   up   variation [GeV]"),
    "energyScaleSystDown": ("egmScaleSystDn",   "energy scale, systematic   down variation [GeV]"),
    "energyScaleGainUp":   ("egmScaleGainUp",   "energy scale, gain-switch  up   variation [GeV]"),
    "energyScaleGainDown": ("egmScaleGainDn",   "energy scale, gain-switch  down variation [GeV]"),
    "energySigmaRhoUp":    ("egmResolRhoUp",    "energy resolution, rho     up   variation [GeV]"),
    "energySigmaRhoDown":  ("egmResolRhoDn",    "energy resolution, rho     down variation [GeV]"),
    "energySigmaPhiUp":    ("egmResolPhiUp",    "energy resolution, phi     up   variation [GeV]"),
    "energySigmaPhiDown":  ("egmResolPhiDn",    "energy resolution, phi     down variation [GeV]"),
    "energyScaleValue":    ("egmScaleValue",    "nominal energy scale correction applied"),
    "energySigmaValue":    ("egmResolValue",    "nominal energy resolution smearing applied"),
    "ecalEnergyPostCorr":  ("egmEnergyPostCorr", "ECAL-only energy after EGM scale&smearing [GeV]; "
                                                 "the reference for the PHOTON variations"),
}


def _addEgmScaleSmearVars(process):
    from PhysicsTools.NanoAOD.common_cff import Var
    for tbl, extra in ((getattr(process, "electronTable", None),
                        {"ecalTrkEnergyPostCorr": ("egmEnergyTrkPostCorr",
                                                   "combined ECAL+track energy after EGM correction [GeV]; "
                                                   "the reference for the ELECTRON variations"),
                         "ecalTrkEnergyErrPostCorr": ("egmEnergyTrkErrPostCorr",
                                                      "error on the combined ECAL+track corrected energy [GeV]")}),
                       (getattr(process, "photonTable", None), {})):
        if tbl is None:
            continue
        for uf, (name, doc) in list(_EGM_SYST.items()) + list(extra.items()):
            # guarded: an object without the userFloat gets the sentinel rather than an exception
            setattr(tbl.variables, name,
                    Var("?hasUserFloat('%s')?userFloat('%s'):-999." % (uf, uf), float,
                        precision=14, doc=doc))
    return process


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

    # --- the two GSF tracks of the merged electron -------------------------------
    # The H->ee gamma analysis rebuilds the merged candidate from both tracks: its mass is
    # the di-track invariant mass, and the track d0/dz/charge/hits drive the PV, opposite-sign
    # and non-conversion cuts plus the per-track scale factors. Publishing them keyed to the
    # electron removes the fragile "match tracks to electrons by exact float equality" step.
    _gsfF = {  # ValueMap<float> label -> (branch name, doc)
        "hdalitzMainGsfPt":     ("gsfMainTrkPt",     "pt of the electron's own GSF track"),
        "hdalitzMainGsfEta":    ("gsfMainTrkEta",    "eta of the electron's own GSF track"),
        "hdalitzMainGsfPhi":    ("gsfMainTrkPhi",    "phi of the electron's own GSF track"),
        "hdalitzMainGsfD0":     ("gsfMainTrkD0",     "dxy(PV) of the electron's own GSF track"),
        "hdalitzMainGsfDz":     ("gsfMainTrkDz",     "dz(PV) of the electron's own GSF track"),
        "hdalitzAddGsfPt":      ("gsfAddTrkPt",      "pt of the additional (second) GSF track"),
        "hdalitzAddGsfEta":     ("gsfAddTrkEta",     "eta of the additional (second) GSF track"),
        "hdalitzAddGsfPhi":     ("gsfAddTrkPhi",     "phi of the additional (second) GSF track"),
        "hdalitzAddGsfD0":      ("gsfAddTrkD0",      "dxy(PV) of the additional GSF track"),
        "hdalitzAddGsfDz":      ("gsfAddTrkDz",      "dz(PV) of the additional GSF track"),
        "hdalitzGsfPtRatio":    ("gsfPtRatio",       "pt(add GSF)/pt(main GSF)"),
        "hdalitzGsfDeltaR":     ("gsfDeltaR",        "dR between the two GSF tracks"),
        "hdalitzGsfRelPtRatio": ("gsfRelPtRatio",    "pt(sum of GSF tracks)/SC raw energy"),
        "hdalitzGsfPtSum":      ("gsfPtSum",         "pt(main GSF) + pt(add GSF)"),
        "hdalitzDiTrkPt":       ("gsfDiTrkPt",       "pt of the two-GSF-track system"),
        "hdalitzDiTrkMass":     ("gsfDiTrkMass",     "invariant mass of the two GSF tracks "
                                                     "(the merged-electron mass used downstream)"),
    }
    _gsfI = {
        "hdalitzMainGsfCharge":    ("gsfMainTrkCharge",    "charge of the electron's own GSF track"),
        "hdalitzMainGsfMissHits":  ("gsfMainTrkMissHits",  "missing inner hits, own GSF track"),
        "hdalitzMainGsfLostHits":  ("gsfMainTrkLostHits",  "lost inner hits, own GSF track"),
        "hdalitzMainGsfPixelHits": ("gsfMainTrkPixelHits", "valid pixel hits, own GSF track"),
        "hdalitzMainGsfLayers":    ("gsfMainTrkLayers",    "tracker layers with measurement, own GSF track"),
        "hdalitzAddGsfCharge":     ("gsfAddTrkCharge",     "charge of the additional GSF track"),
        "hdalitzAddGsfMissHits":   ("gsfAddTrkMissHits",   "missing inner hits, additional GSF track"),
        "hdalitzAddGsfLostHits":   ("gsfAddTrkLostHits",   "lost inner hits, additional GSF track"),
        "hdalitzAddGsfPixelHits":  ("gsfAddTrkPixelHits",  "valid pixel hits, additional GSF track"),
        "hdalitzAddGsfLayers":     ("gsfAddTrkLayers",     "tracker layers with measurement, additional GSF track"),
        "hdalitzHasAddGsf":        ("gsfHasAddTrk",        "an additional (second) GSF track was found"),
    }
    for label, (name, doc) in _gsfF.items():
        setattr(ev, name, ExtVar(cms.InputTag("hdalitzMergedID", label), float, doc=doc, precision=14))
    for label, (name, doc) in _gsfI.items():
        setattr(ev, name, ExtVar(cms.InputTag("hdalitzMergedID", label), "int", doc=doc))

    _addMergedEleInputVars(process)

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


# per-year entry points running BOTH IDs (cmsDriver --customise takes a single dotted name)
def customizeAllMergedElectron2016APV(process):
    return customizeAllMergedElectron(process, "2016APV")


def customizeAllMergedElectron2016(process):
    return customizeAllMergedElectron(process, "2016")


def customizeAllMergedElectron2017(process):
    return customizeAllMergedElectron(process, "2017")


def customizeAllMergedElectron2018(process):
    return customizeAllMergedElectron(process, "2018")
