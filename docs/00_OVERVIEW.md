# Overview — porting the merged-electron ID into a customized NanoAOD

## Goal (one sentence)

Take the **merged-electron identification** from
[SanghyunKo/ZprimeTo4l](https://github.com/SanghyunKo/ZprimeTo4l) and expose its output as
two extra branches on the NanoAOD `Electron` table, in two CMSSW release lines
(`CMSSW_10_6_X` and `CMSSW_15_0_X`), both targeting Run2 UL.

## Scope boundary

| Ported | Not ported |
|--------|-----------|
| `ModifiedHEEP` value-map producer + helpers | `Analysis/` CR analyzers (Resolved/Merged Ele/Mu/EMu) |
| `MergedLepton` ID producer + GBRForest MVA + `data/` models | Fake-rate estimation (`estimate*`, `run*FF.cc`) |
| A new `NanoDalitz` nano-customization package | Muon Rochester / `RoccoR`, electron S&S systematics |
| `Electron_mvaMergedElectron`, `Electron_mvaMergedElectronCategory` branches | combine/ datacards, plotting, HEPData |

Per the user: *"we just need the ID part of the game → port the ID as an electron branch."*
Everything downstream of the ID (the physics selection) is expected to happen on the
customized NanoAOD, outside this CMSSW package.

## What the ID actually is

The merged-electron MVA targets `GsfElectron`s that are really **two overlapping electrons**
(e.g. from a low-mass/boosted → e⁺e⁻ Dalitz-like topology). It reconstructs a "second track"
and second-cluster observables, then scores the object with a GBRForest. It is **barrel
(EB) only** and split into two categories:

- `HasTrk` — a second GSF/KF track is associated and Et > 20 GeV.
- `NoTrkEt2` — no second track.
- `Nulltype = -1` — not applicable (e.g. endcap); no physical score.

Each category has its own weights (`data/{HasTrk,NoneEt2}_EB_20ULYY.xml`) and input
mean/std scaling (`..._EB_20ULYY.csv`), per UL year (`20UL16APV`, `20UL16`, `20UL17`,
`20UL18`).

## Producer chain and data flow

```
MINIAOD inputs
  slimmedElectrons
  reducedEgamma:reducedGsfTracks, reducedEBRecHits, reducedEERecHits
  packedPFCandidates, lostTracks, lostTracks:eleTracks
  offlineBeamSpot
EventSetup
  GeometryRecoDB, MagneticField, TransientTrackBuilder,
  EcalSeverityLevelESProducer, GlobalTag
        │
        ▼  (ModifiedHEEP package)
ModifiedHEEPIDVarValueMaps  = EDProducer("ModifiedHEEPIDValueMapProducer")
  helper classes: ModifiedDEtaInSeed, ModifiedShowerShape,
                  ModifiedEleTkIsolFromCands, ModifiedRecHitIsolation
  outputs (all ValueMap keyed to slimmedElectrons):
    float  : dPerpIn, dEtaInSeed2nd, dPhiInSC2nd, alphaTrack, alphaCalo,
             normalizedDParaIn, union5x5covIeIe, union5x5covIeIp,
             union5x5covIpIp, union5x5dEtaIn, union5x5dPhiIn, ...
    ref    : eleAddGsfTrk (GsfTrackRef), eleAddPackedCand (PackedCandidateRef)
        │
        ▼  (MergedLepton package)
mergedLeptonIDProducer<year>  = EDProducer("MergedLeptonIDProducer")
  MergedMvaEstimator loads GBRForest via createGBRForest (CommonTools/MVAUtils)
  outputs (ValueMap keyed to slimmedElectrons):
    float  "mvaMergedElectronValues"     (sigmoid score)
    int    "mvaMergedElectronCategories"
        │
        ▼  (NanoDalitz package — new)
electronTable.externalVariables +=
    Electron_mvaMergedElectron         (float)
    Electron_mvaMergedElectronCategory (int8)
```

The `MergedLeptonIDProducer` consumes **only** the `ModifiedHEEPIDVarValueMaps` outputs +
`slimmedElectrons` + the model files. Note this means `ModifiedEcalRecHitIsolationScone`
(used by upstream *analyzers*) is **not** required for the score, and is dropped.

## Key facts that de-risk the port

1. **MVA backend is standard CMSSW.** `MergedMvaEstimator` uses `GBRForest` +
   `createGBRForest` from `CommonTools/MVAUtils` (exists in both 10_6 and 15_0). The `.xml`
   are already GBRForest/TMVA format (upstream converted xgboost via `xgboost2tmva.py`).
   No XGBoost at runtime → nothing to migrate on the MVA side.
2. **Isolation math is self-contained.** `ModifiedEleTkIsolFromCands`,
   `ModifiedRecHitIsolation`, `ModifiedShowerShape`, `ModifiedDEtaInSeed` are in-package
   forks of egamma tools, so they are insulated from upstream egamma API churn. The port's
   compile risk is concentrated in EventSetup/handle access, not in the physics helpers.
3. **The ValueMap→table attachment is a solved pattern.** Stock NanoAOD already attaches
   egamma value maps (keyed to `slimmedElectrons`) to the `Electron` table (which iterates
   `finalElectrons`, preserving refs). Reuse `electronTable.externalVariables` +
   `ExtVar`; do not invent matching.
4. **A working template exists.** `DickyChant/BPHNano` (→ `PhysicsTools/BPHNano`) shows the
   full shape of a customized-nano package (plugins + `_cff` + `nano*_cff` customise +
   `test/`). `NanoDalitz` copies that shape.

## Design decisions (apply to both branches)

- **Package layout.** Keep `ZprimeTo4l/ModifiedHEEP` and `ZprimeTo4l/MergedLepton` names
  unchanged (so `FileInPath`/includes resolve). Add one new package for nano glue. Two
  acceptable homes:
  - `ZprimeTo4l/NanoDalitz` (keeps everything under one group), or
  - `PhysicsTools/NanoDalitz` (matches BPHNano convention, next to `PhysicsTools/NanoAOD`).
  Recommend `PhysicsTools/NanoDalitz` for the nano glue to sit beside `PhysicsTools/NanoAOD`
  and match the user's BPHNano muscle memory, while the producers stay under `ZprimeTo4l/`.
- **Year selection.** Drive the `mergedLeptonIDProducer<year>` clone and GlobalTag from a
  `year` argument on the customise function (default from `--era`). Never hardcode UL16.
- **Endcap sentinel.** EE electrons get category `-1` and score `-1` (document in the branch
  doc string). Keep the table dense (one entry per electron) so indexing stays trivial.
- **No new event content beyond the two branches** unless explicitly requested. The
  intermediate `ModifiedHEEPIDVarValueMaps` floats can optionally be exposed later as debug
  branches behind a flag, but are off by default.

## Deliverables per branch

1. Compiling `ModifiedHEEP` + `MergedLepton` producer libraries.
2. `PhysicsTools/NanoDalitz` with:
   - `python/mergedElectronID_cff.py` — ES + both producers, per-year clones.
   - `python/nano_cff.py` — `customizeMergedElectron(process, year=...)`.
   - `test/run_nanoDalitz_cfg.py` (or a `cmsDriver` command in the README).
   - `test/validate_nano.py` — asserts branches exist and are filled for EB electrons.
3. A short branch `README`/notes capturing the exact GlobalTag + era used for validation.

## Milestones

- **M0** — repo scaffolding + this plan (done here).
- **M1 (10_6)** — producers compile; customized nano builds; branches appear on a DY MC
  MINIAOD test file. This is the reference implementation.
- **M2 (15_0)** — same, after the API migration checklist in `PLAN_CMSSW_15_0.md`.
- **M3** — validation on DY MC (score distribution sane, EB-only, category populated);
  cross-check a handful of events against the 10_6 output. *(User: "not there yet.")*

## Sources consulted

- Upstream code: `SanghyunKo/ZprimeTo4l@master` (`ModifiedHEEP/`, `MergedLepton/`).
- Base: `DickyChant/cmssw` (branch `CMSSW_10_6_X`), `DickyChant/BPHNano@main`.
