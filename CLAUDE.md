# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`customized_nano_dalitz` ports the **merged-electron identification** from
[SanghyunKo/ZprimeTo4l](https://github.com/SanghyunKo/ZprimeTo4l) into a **customized
NanoAOD**. The single deliverable is: run the merged-electron ID producer chain over
MINIAOD and attach its output (an MVA score + a category) as **extra branches on the
NanoAOD `Electron` table** — nothing more. The Z'→4l control-region analyzers, fake-rate
estimation, muon/Rochester corrections, and combine/plotting tooling from upstream are
**out of scope** and are not ported.

"Dalitz" refers to the physics motivation: low-mass / boosted lepton pairs whose two
electrons merge into a single reconstructed `GsfElectron`. The merged-electron MVA is the
tool that recovers those objects, and it is barrel-only (EB) in the upstream models.

This is a **CMSSW** package. It is not buildable or testable outside a CMSSW release area;
there is no CMSSW in this Claude environment, so code here is authored and reviewed, then
compiled/run by the user inside `$CMSSW_BASE/src`.

## Base software (use the user's forks)

Build against the user's CMSSW fork and reuse the user's customized-NanoAOD template:

- **CMSSW fork:** `github.com/DickyChant/cmssw`. The `CMSSW_10_6_X` branch is the base for
  the 10_6 line. There is no clean `CMSSW_15_0_X` nano branch on the fork yet (existing
  nano branches are `hin_nanoaod_15_1_X` and `backport/fix_angantyr-CMSSW_15_0_X`); the
  15_0 work should branch off a `CMSSW_15_0_X` IB / the fork and follow the same layout.
- **Custom-NanoAOD template:** `github.com/DickyChant/BPHNano` (cloned into
  `$CMSSW_BASE/src/PhysicsTools/BPHNano`). It is the structural precedent for this project:
  custom `SimpleFlatTableProducer` plugins under `plugins/`, `_cff.py` builders, a
  top-level `nano<X>_cff.py` that assembles the sequence + `--customise` functions, and
  `test/run_*_cfg.py` + `test/validate_nano.py`. Mirror this layout for `NanoDalitz`.
- Not needed: `DickyChant/XGBoostCMSSW` and `EgammaWork` — the merged MVA runs through
  `GBRForest` (`CommonTools/MVAUtils`), so no XGBoost runtime interface is required.

## Two release branches

The work is split across two git branches, both targeting **Run2 UL** data/MC:

| Branch | Release | NanoAOD era | Status |
|--------|---------|-------------|--------|
| `CMSSW_10_6_X` | 10.6.39 (upstream's native release) | NanoAODv9 | plugins reused nearly verbatim |
| `CMSSW_15_0_X` | 15.0.X | NanoAODv14/v15 | plugins migrated to modern APIs; Run3 works out of the box |

Run2 is the target for both. On `CMSSW_15_0_X`, Run3 MINIAOD is expected to work with no
extra effort (same MINIAOD collection names, newer conditions) — see the plan doc.

## Repository layout intent

The repo root maps onto the CMSSW package group `ZprimeTo4l`, i.e. it is meant to be
cloned into `$CMSSW_BASE/src/ZprimeTo4l`. Only the subpackages needed for the ID are kept:

- `ModifiedHEEP/` — `ModifiedHEEPIDValueMapProducer` + its helper classes
  (`ModifiedDEtaInSeed`, `ModifiedShowerShape`, `ModifiedEleTkIsolFromCands`,
  `ModifiedRecHitIsolation`). Produces the per-electron `ValueMap`s the MVA consumes.
- `MergedLepton/` — `MergedLeptonIDProducer` + `MergedMvaEstimator` (GBRForest wrapper)
  + the `data/*.xml` (GBRForest weights) and `data/*.csv` (input mean/std scaling),
  per UL year (`20UL16APV`, `20UL16`, `20UL17`, `20UL18`).
- `NanoDalitz/` — **new package added by this project**: the NanoAOD customization
  (`python/nano_cff.py`) that wires the producer chain into the standard nano sequence
  and extends the `Electron` table. This is where most net-new code lives.

Keep the `ZprimeTo4l/ModifiedHEEP` and `ZprimeTo4l/MergedLepton` package names unchanged
so that `edm::FileInPath("ZprimeTo4l/MergedLepton/data/...")` and `#include
"ZprimeTo4l/..."` paths in the upstream sources continue to resolve without edits.

## The producer chain (what actually gets ported)

```
slimmedElectrons + reducedEgamma:{reducedGsfTracks,reducedEBRecHits,reducedEERecHits}
   + packedPFCandidates + lostTracks(:eleTracks) + offlineBeamSpot
        │
        ▼
ModifiedHEEPIDVarValueMaps   (EDProducer "ModifiedHEEPIDValueMapProducer")
   → ValueMap<float>: dPerpIn, dEtaInSeed2nd, dPhiInSC2nd, alphaTrack, alphaCalo,
       normalizedDParaIn, union5x5covIeIe/IeIp/IpIp, union5x5dEtaIn/dPhiIn, ...
   → ValueMap<GsfTrackRef> eleAddGsfTrk, ValueMap<PackedCandidateRef> eleAddPackedCand
        │
        ▼
mergedLeptonIDProducer       (EDProducer "MergedLeptonIDProducer", per-year clone)
   → ValueMap<float> "mvaMergedElectronValues"     (sigmoid score, EB only)
   → ValueMap<int>   "mvaMergedElectronCategories" (HasTrk / NoTrkEt2 / Nulltype)
        │
        ▼
NanoDalitz table extension   → Electron_mvaMergedElectron (float)
                             → Electron_mvaMergedElectronCategory (int8)
```

`MergedMvaEstimator` loads the model with `createGBRForest` (`CommonTools/MVAUtils`), so
the runtime dependency is standard CMSSW — there is **no XGBoost runtime dependency**; the
`.xml` files are already GBRForest/TMVA format. The MVA uses two EB categories
(`HasTrk`: a second track and Et>20 GeV present; `NoTrkEt2`: no second track), each with
its own weights + scaling file.

Required EventSetup: `Configuration.Geometry.GeometryRecoDB`, `MagneticField`,
`TransientTrackBuilder`, `EcalSeverityLevelESProducer`, and a matching GlobalTag
(e.g. `106X_mcRun2_asymptotic_v13` for UL16 MC).

## NanoAOD integration pattern

The `ValueMap`s are keyed to `slimmedElectrons`; the nano `Electron` table iterates
`finalElectrons` (`linkedObjects:electrons`), which preserves refs back to
`slimmedElectrons`. This is exactly how stock nano attaches egamma MVA value maps, so the
integration reuses that proven mechanism: run the producers on `slimmedElectrons`, then add
the value maps to `electronTable.externalVariables` via `ExtVar`. Do **not** invent a new
matching scheme.

Integration is delivered as a cmsDriver customise function, e.g.:

```
--customise ZprimeTo4l/NanoDalitz/nano_cff.customizeMergedElectron
```

which (1) loads the ES + both producers, (2) inserts them into the nano task ahead of
`electronTable`, (3) appends the two external variables to `electronTable`.

## Build & run (inside a CMSSW area — not runnable here)

Setup mirrors upstream but drops the Egamma S&S / TnP clones (analysis-only), builds
against the user's CMSSW fork, and adds `PhysicsTools/NanoAOD`. For `CMSSW_10_6_X`:

```sh
cmsrel CMSSW_10_6_39 && cd CMSSW_10_6_39/src && cmsenv && git cms-init
git cms-addpkg PhysicsTools/NanoAOD
git clone -b CMSSW_10_6_X https://github.com/DickyChant/customized_nano_dalitz ZprimeTo4l
scram b -j8
```

Produce a customized NanoAOD from a MINIAOD test file (DY MC is the intended test sample —
not yet wired up):

```sh
cmsDriver.py nano_dalitz -s NANO --mc --era Run2_2018 \
  --conditions 106X_upgrade2018_realistic_v16 \
  --customise ZprimeTo4l/NanoDalitz/nano_cff.customizeMergedElectron \
  --filein file:DY_MiniAOD.root --fileout file:nano_dalitz.root -n 1000
```

Verify the port by confirming the new branches exist and are filled for barrel electrons:

```sh
python3 -c "import ROOT; e=ROOT.RDataFrame('Events','nano_dalitz.root'); \
  print(e.Filter('nElectron>0').Mean('Electron_mvaMergedElectron').GetValue())"
```

For `CMSSW_15_0_X`, use `cmsrel CMSSW_15_0_X`, the matching UL18 (or Run3) GlobalTag, and
the same `--customise` path. Expect to fix compile errors from EventSetup token migration
first — see `docs/PLAN_CMSSW_15_0.md`.

## Where this actually runs: FNAL LPC (cmslpc)

Development and grid production happen on **cmslpc**, native el9 (`el9_amd64_gcc12`) — the 15_0
branch needs no container. `scripts/build_lpc_150.sh` creates
`/uscms_data/d3/sitianq/nu_dalitz/CMSSW_15_0_20` and rsyncs `ZprimeTo4l/`, `PhysicsTools/` and
`HDalitzEle/` in from this repo; re-run it after editing package code.

CRAB submission lives in `crab/` and is LPC-configured (proxy under `/uscms/home/$USER/`,
`T3_US_FNALLPC`, golden JSONs vendored in `crab/jsons/`). **Read `crab/README.md` before
submitting anything** — it carries the storage/quota checks, the memory-sizing rule, the
multithreading measurements and the production gotchas. Key points that bite:

- **Storage is the binding constraint.** `/store/user/sqian` on FNAL EOS is a symlink to
  `/store/user/sitianq`; one ~2 TB quota, already ~92% full. The full AN-21-053 set is ~7-10 TB
  and belongs at **IHEP / T2_CN_Beijing** (509 TB free), via `CND_SITE` + `CND_OUTLFN`.
- **Memory** = `max(measured need, numCores * 2000 MB)` — 2 GB/core is the minimal grid slot, so
  asking less buys nothing and asking more narrows site matching. Under-requesting gets jobs
  killed with exit 50660.
- **Threading is validated**: 1/2/4-thread output is bit-identical across all six merged-ID
  branches, and 4 threads runs ~3.8x faster on the event loop for ~+900 MB. Benchmark with
  `scripts/bench_threads.sh` (writes to the 3DayLifetime scratch, not the project area).
- Scratch for large test files: `/uscmst1b_scratch/lpc1/3DayLifetime/$USER/`.

## Planning docs

Read these before implementing — they contain the actual step-by-step work and the API
migration checklist:

- `docs/00_OVERVIEW.md` — upstream→port mapping, scope boundary, shared design decisions.
- `docs/PLAN_CMSSW_10_6.md` — the straightforward native port + nano wiring.
- `docs/PLAN_CMSSW_15_0.md` — the same, plus the 10_6→15_0 API migration checklist.

## Conventions

- Preserve upstream file/class/module names and the `ZprimeTo4l/<Pkg>` include roots; the
  only net-new package is `NanoDalitz`.
- Per-year model selection is done by cloning `mergedLeptonIDProducer` (the upstream
  `_cfi.py` already defines `...20UL16APV/16/17/18` clones); the nano customise function
  picks the clone from the `--era` / a `year` argument. Do not hardcode UL16.
- The merged-electron MVA is **EB-only**; endcap electrons get a sentinel (upstream uses
  category `Nulltype = -1` and does not fill a physical score). Preserve that semantics in
  the branch (document the sentinel value chosen).
