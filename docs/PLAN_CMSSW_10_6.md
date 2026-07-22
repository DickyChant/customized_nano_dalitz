# Plan — `CMSSW_10_6_X` branch (reference implementation)

This is the native release of the upstream package, so the producers compile almost
verbatim. The work is mostly (a) trimming to the ID subset and (b) writing the NanoAOD
glue. Build against `DickyChant/cmssw@CMSSW_10_6_X`. Target NanoAODv9, Run2 UL.

## Step 0 — release area

```sh
cmsrel CMSSW_10_6_39 && cd CMSSW_10_6_39/src && cmsenv && git cms-init
git cms-addpkg PhysicsTools/NanoAOD
# our packages (this repo, checked out at branch CMSSW_10_6_X):
git clone -b CMSSW_10_6_X https://github.com/DickyChant/customized_nano_dalitz ZprimeTo4l
scram b -j8
```

`ZprimeTo4l/` provides `ModifiedHEEP/` and `MergedLepton/`. The nano glue lives in
`PhysicsTools/NanoDalitz/` (added by this repo, see Step 2). If it is simpler to keep one
group, put it under `ZprimeTo4l/NanoDalitz/` instead — either resolves.

## Step 1 — bring over the ID producers (trimmed)

Copy from upstream `master`, keeping paths/namespaces identical:

- `ModifiedHEEP/` — `interface/`, `src/`, `plugins/{ModifiedHEEPIDValueMapProducer.cc,
  ModifiedEcalRecHitIsolationProducer.cc, cuts/*}`, `python/{ModifiedHEEPIdVarValueMapProducer_cfi,
  ModifiedElectronTrackIsolations_cfi, ModifiedEcalRecHitIsolationScone_cfi}.py`, both
  `BuildFile.xml`.
  - `ModifiedEcalRecHitIsolationProducer` + its `_cfi` are **not needed** by the MVA score.
    Keep them only if a modified-HEEP VID cut you also want to expose depends on them;
    otherwise omit to shrink the build.
- `MergedLepton/` — `interface/{MergedMvaEstimator.h, MergedLeptonHelper.h}`,
  `src/{MergedMvaEstimator.cc, MergedLeptonHelper.cc}`,
  `plugins/{MergedLeptonIDProducer.cc, cuts/GsfEleDPtOverPtCut.cc}`,
  `python/MergedLeptonIDProducer_cfi.py`, `data/{HasTrk,NoneEt2}_EB_20UL*.{xml,csv}`,
  `BuildFile.xml`.
  - Drop the analyzers (`MergedEle*Analyzer.cc`, `MergedLeptonID*Analyzer.cc`,
    `MergedEle*MvaInput.cc`) and their `_cfi`/`test/` — they are training/validation tools,
    not the ID.
  - `MergedLeptonHelper` is only needed if a kept plugin includes it; if
    `MergedLeptonIDProducer.cc` does not, drop it too. Verify with the include graph.

Verify the trimmed set compiles: `scram b -j8`. Nothing here should need code edits in
10_6 — it is the upstream's own release.

## Step 2 — `PhysicsTools/NanoDalitz` (the new package)

Mirror `DickyChant/BPHNano`'s package shape.

### 2a. `python/mergedElectronID_cff.py`

Assemble the ES + producer chain and expose per-year sequences.

```python
import FWCore.ParameterSet.Config as cms

# EventSetup the producers need (these ES modules are otherwise absent from a NANO job)
from Configuration.StandardSequences.MagneticField_cff import *          # or load in customise
# TransientTrackBuilder + EcalSeverityLevel are pulled in via process.load in the customise fn

from ZprimeTo4l.ModifiedHEEP.ModifiedHEEPIdVarValueMapProducer_cfi import ModifiedHEEPIDVarValueMaps
from ZprimeTo4l.MergedLepton.MergedLeptonIDProducer_cfi import (
    mergedLeptonIDProducer, mergedLeptonIDProducer20UL16APV,
    mergedLeptonIDProducer20UL17, mergedLeptonIDProducer20UL18)

# point producers at the MINIAOD electron collection (upstream _cfi already uses slimmedElectrons)
_producerByYear = {
    "2016APV": mergedLeptonIDProducer20UL16APV,
    "2016":    mergedLeptonIDProducer,          # 20UL16 = default clone
    "2017":    mergedLeptonIDProducer20UL17,
    "2018":    mergedLeptonIDProducer20UL18,
}

def mergedElectronIDTask(year="2018"):
    merged = _producerByYear[year].clone()
    return cms.Task(ModifiedHEEPIDVarValueMaps, merged), merged
```

Note the upstream `MergedLeptonIDProducer_cfi` sets `srcEle=slimmedElectrons` with
`skipCurrentProcess()`; keep that so it reads the input MINIAOD collection, not a
re-made one.

### 2b. `python/nano_cff.py` — the customise function

```python
import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import ExtVar
from PhysicsTools.NanoDalitz.mergedElectronID_cff import mergedElectronIDTask

def customizeMergedElectron(process, year="2018"):
    # ES the producers need but a NANO job lacks
    process.load("Configuration.StandardSequences.MagneticField_cff")
    process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
    process.load("RecoLocalCalo.EcalRecAlgos.EcalSeverityLevelESProducer_cfi")

    task, merged = mergedElectronIDTask(year)
    process.mergedElectronIDTask = task

    # attach to the standard nano electron table (iterates finalElectrons, keeps refs to slimmedElectrons)
    process.electronTable.externalVariables.mvaMergedElectron = ExtVar(
        cms.InputTag("%s:mvaMergedElectronValues" % merged.label()), float,
        doc="merged-electron MVA score (EB only; -1 if N/A)", precision=14)
    process.electronTable.externalVariables.mvaMergedElectronCategory = ExtVar(
        cms.InputTag("%s:mvaMergedElectronCategories" % merged.label()), "int8",
        doc="merged-electron MVA category (-1 Null, 0 HasTrk, 1 NoTrkEt2)")

    # make the producers run before the table is filled
    process.nanoTableTaskCommon.add(process.mergedElectronIDTask)   # or the era's task
    return process
```

Details to get right (verify against the 10_6 `PhysicsTools/NanoAOD` you actually have):

- **Where the table lives.** In NanoAODv9/10_6, the electron table module is
  `process.electronTable` and its source iterates `linkedObjects:electrons`
  (`finalElectrons`). `externalVariables` accepts `ExtVar` keyed by a ValueMap on the
  original `slimmedElectrons` — the ref chain resolves. Confirm the exact task name to
  `.add()` into (`nanoTableTaskCommon` / `electronTask` / `nanoSequenceCommon` depending on
  the release's cff).
- **`int8` external var.** If the 10_6 `ExtVar` does not support `"int8"`, store the category
  as `int` (bigger branch) or as `float`; prefer the smallest integer type the release's
  `FlatTableProducer` supports.
- **`year` plumbing.** cmsDriver `--customise_commands` can pass the year, or expose a second
  customise entry point per year (`customizeMergedElectron2017`, ...) that just calls the
  base with the right argument — matches how BPHNano exposes era variants.

### 2c. `plugins/`

For the minimal deliverable, **no new plugin is required** — the two branches come straight
off the existing ValueMaps via `ExtVar`. Only add a `SimpleFlatTableProducer`-style plugin
(à la BPHNano) if you later want a *separate* MergedElectron table (e.g. to also carry the
`ModifiedHEEPIDVarValueMaps` debug floats). Keep that behind a flag; off by default.

## Step 3 — test config + validation

`test/run_nanoDalitz_cfg.py` — either a hand-written cfg (like BPHNano's
`test/run_bphNano_cfg.py`) or, simpler, document the cmsDriver command in the README:

```sh
cmsDriver.py nano_dalitz -s NANO --mc --era Run2_2018 \
  --conditions 106X_upgrade2018_realistic_v16 \
  --customise PhysicsTools/NanoDalitz/nano_cff.customizeMergedElectron \
  --customise_commands 'process=customizeMergedElectron(process,year="2018")' \
  --filein file:DY_MiniAOD.root --fileout file:nano_dalitz.root -n 1000
```

(Choose the GlobalTag/era to match the DY MINIAOD sample's campaign — UL16APV/16/17/18.)

`test/validate_nano.py` — assert the branches exist, are the right type, are filled for EB
electrons, and carry the sentinel elsewhere:

```python
import ROOT
df = ROOT.RDataFrame("Events", "nano_dalitz.root")
assert "Electron_mvaMergedElectron" in [str(c) for c in df.GetColumnNames()]
eb = df.Filter("nElectron>0 && abs(Electron_eta[0])<1.479")
print("mean EB score:", eb.Mean("Electron_mvaMergedElectron").GetValue())
print("category counts:", df.Histo1D("Electron_mvaMergedElectronCategory").GetValue().GetEntries())
```

## Risk / watch-list (10_6)

- **Missing ES in a NANO-only job.** A stock NANO step does not load MagneticField /
  TransientTrackBuilder / EcalSeverityLevel; the customise fn must, or the producers throw
  at `beginRun`/`produce`. (Confirmed needed from upstream `runMergedAnalyzer_cfg.py`.)
- **RecHit inputs must survive in the MINIAOD.** Producers read
  `reducedEgamma:reducedEBRecHits/reducedEERecHits`; standard UL MINIAOD has them. If a
  custom/skimmed MINIAOD dropped `reducedEgamma`, the port cannot run.
- **Task ordering.** The ValueMap producers must be in the scheduled Task *before*
  `electronTable`; putting them only in a `Sequence` that nano doesn't run will silently
  leave the branch unfilled. Use the `Task` + `.add()` into the nano task.
- **Endcap / category −1.** Ensure the branch is written for every electron (dense), with a
  documented sentinel, so downstream indexing is safe.

## Definition of done (M1)

`scram b` clean; the cmsDriver command above produces `nano_dalitz.root` with
`Electron_mvaMergedElectron` + `Electron_mvaMergedElectronCategory`; `validate_nano.py`
passes on a DY MC file; EB electrons have a physical score in [0,1], EE electrons the
sentinel.
