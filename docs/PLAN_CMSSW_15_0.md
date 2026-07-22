# Plan — `CMSSW_15_0_X` branch

Same deliverable as the 10_6 plan (two Electron branches from the merged-electron MVA), but
the upstream producers were written for 10_6 and must be **migrated to modern CMSSW APIs**
before they compile in 15_0. Target NanoAODv14/v15. **Run2 UL is the goal**; the same code
is expected to run on **Run3 MINIAOD out of the box** because the input collection names
(`slimmedElectrons`, `reducedEgamma:*`, `packedPFCandidates`, `lostTracks`) are unchanged —
only the era/GlobalTag differ.

Do the 10_6 branch first: it is the reference whose output the 15_0 port is validated
against.

## Step 0 — release area

```sh
cmsrel CMSSW_15_0_X && cd CMSSW_15_0_X/src && cmsenv && git cms-init
git cms-addpkg PhysicsTools/NanoAOD
git clone -b CMSSW_15_0_X https://github.com/DickyChant/customized_nano_dalitz ZprimeTo4l
scram b -j8    # expect compile errors → work the migration checklist below
```

`DickyChant/cmssw` has no `CMSSW_15_0_X` nano branch yet (only `hin_nanoaod_15_1_X`,
`backport/fix_angantyr-CMSSW_15_0_X`). Use the official `CMSSW_15_0_X` IB unless the user
wants a fork branch; if their fork carries needed patches, branch our work off it.

## Step 1 — API migration checklist (the real work)

Port `ModifiedHEEP` + `MergedLepton` source. The physics helpers
(`ModifiedEleTkIsolFromCands`, `ModifiedRecHitIsolation`, `ModifiedShowerShape`,
`ModifiedDEtaInSeed`) are in-package forks, so most breakage is framework-level, concentrated
in EventSetup access. Work top-down; each item is "audit → likely change":

1. **EventSetup → esConsumes tokens (highest-impact).** 10_6 code that does
   `edm::ESHandle<T> h; iSetup.get<Record>().get(h);` is removed in modern CMSSW. Replace with
   a token member `edm::ESGetToken<T,Record> tok_;` initialized in the constructor via
   `esConsumes()` and read with `auto const& x = iSetup.getData(tok_);`. Apply to every ES
   product the producers use: `CaloGeometry`/`CaloTopology`
   (`CaloGeometryRecord`/`CaloTopologyRecord`), `MagneticField` (`IdealMagneticFieldRecord`),
   `TransientTrackBuilder` (`TransientTrackRecord`, label `TransientTrackBuilder`),
   `EcalSeverityLevelAlgo` (`EcalSeverityLevelAlgoRcd`), Ecal channel-status/ped conditions
   if referenced. Grep the sources for `iSetup.get`, `ESHandle`, `.get(` on records.
2. **`consumes` already token-based** in this code (constructor `consumes<...>()`), so event
   `getByToken` should be fine. Confirm no lingering `getByLabel`.
3. **Egamma tool signatures.**
   - `EcalClusterLazyTools` / `noZS::EcalClusterLazyTools` constructor now takes
     `esConsumes`-provided tokens (a `ESGetTokens` bundle) instead of `EventSetup`. If
     `ModifiedShowerShape`/`ModifiedDEtaInSeed` build lazy tools, thread tokens through.
   - `EleTkIsolFromCands` upstream evolved (`TrkCuts`/`Configuration` struct, `barrelCuts`/
     `endcapCuts`). Our `ModifiedEleTkIsolFromCands` is a **fork**, so it does not track those
     changes — but check it does not `#include` an upstream header whose struct layout moved.
     If it does, vendor the needed piece.
   - `PositionCalc` (`RecoEcal/EgammaCoreTools`) — API stable; the `posCalcLog` PSet in the
     `_cfi` should still work.
4. **DataFormats accessors.** `pat::Electron`, `reco::GsfElectron` full5x5 / shower-shape /
   `superCluster()` accessors are stable across 10_6→15_0. Spot-check any removed accessor
   flagged by the compiler.
5. **`GBRForest` / `createGBRForest`.** Header `CommonTools/MVAUtils/interface/GBRForestTools.h`
   and the `.xml` format are unchanged → `MergedMvaEstimator` should compile as-is. This is
   the biggest de-risker: **no MVA rewrite**.
6. **VID cut plugins** (`cuts/GsfEle*Cut.cc`). `CutApplicatorBase` interface + the
   `DEFINE_EDM_PLUGIN(CutApplicatorFactory,...)` registration are stable; only needed if you
   also expose a modified-HEEP boolean. For the minimal MVA-only deliverable, you can defer
   these.
7. **C++ standard / warnings-as-errors.** 15_0 builds with a newer std and stricter flags;
   fix narrowing, `auto` deductions, and any `std::` bits the old code relied on implicitly.
8. **BuildFile deps.** The `<use name=.../>` packages in the upstream BuildFiles still exist
   in 15_0; add any new one the migration introduces (e.g. a `*Record` package). Remove
   `rootcore` if it errors.

Recommended tactic: get `ModifiedHEEP` compiling alone first (`scram b
ZprimeTo4l/ModifiedHEEP`), then `MergedLepton`, then the nano glue.

## Step 2 — `PhysicsTools/NanoDalitz` for 15_0

Structurally identical to the 10_6 plan (`mergedElectronID_cff.py` + `nano_cff.py` +
`test/`), with these differences:

- **Table module + task names.** The v14/v15 electron table is still `process.electronTable`,
  but the surrounding task/sequence names and the `finalElectrons` wiring may differ from
  v9. Inspect the release's `PhysicsTools/NanoAOD/python/electrons_cff.py` and add the
  producer `Task` into whatever task feeds `electronTable` (e.g. `electronTask` /
  `nanoTableTaskCommon`). The **`externalVariables` + `ExtVar` mechanism is unchanged**.
- **`int8` external var** is well-supported in v14/v15 — use it for the category.
- **Precision.** Modern nano uses explicit `precision=` on floats; keep the score at high
  precision (e.g. 14) since it is a discriminant.
- **Era.** For Run2 MINIAOD reprocessed in 15_0 pass `--era Run2_2018` (or the matching UL
  era) and the UL GlobalTag. For Run3, `--era Run3` + a Run3 GlobalTag — the customise
  function and producers need no change (this is the "Run3 out of the box" claim; still
  validate that the per-year *model* selection makes sense — the shipped weights are UL/Run2,
  so a Run3 run reuses the closest UL model unless/until Run3 weights are trained).

## Step 3 — validation & cross-check

Same `test/validate_nano.py` as 10_6. Additionally, **cross-check against the 10_6 output**:
run both releases over the *same* DY UL MINIAOD file and compare
`Electron_mvaMergedElectron` event-by-event for barrel electrons. Small differences are
expected from reconstruction/tool changes between releases; large or structured differences
signal a migration bug (most likely an ES product silently defaulting, or a lazy-tool token
mismatch). Document the observed agreement level in the branch README.

```sh
cmsDriver.py nano_dalitz -s NANO --mc --era Run2_2018 \
  --conditions <UL18_GT_for_15_0> \
  --customise PhysicsTools/NanoDalitz/nano_cff.customizeMergedElectron \
  --customise_commands 'process=customizeMergedElectron(process,year="2018")' \
  --filein file:DY_MiniAOD.root --fileout file:nano_dalitz_15_0.root -n 1000
```

## Risk / watch-list (15_0-specific)

- **Silent ES defaulting.** The single most likely correctness bug: an ES product that used
  to come from `iSetup.get<Record>()` now needs an explicit `esConsumes` token; if a code
  path is missed, you may get a default-constructed/empty object rather than a compile error
  in some cases. The 10_6 cross-check is the guard.
- **Reduced-rechit availability on Run3 MINIAOD.** Confirm `reducedEgamma:reducedEBRecHits`
  still exists with the same instance labels in the Run3 MINIAOD you test.
- **Model provenance on Run3.** The GBRForest weights are Run2/UL. Reusing them on Run3 is a
  physics assumption, not a bug — flag it clearly; a Run3 retraining is future work, out of
  this port's scope.
- **NanoAOD schema version.** Note which nano version (`--nano_version`/`nanoV1X`) the release
  defaults to so the added branches land in a documented schema.

## Definition of done (M2)

`scram b` clean in 15_0; the cmsDriver command produces the two Electron branches on a DY MC
MINIAOD file; `validate_nano.py` passes; a same-file cross-check vs the 10_6 branch shows
consistent EB scores (agreement level documented). Run3 MINIAOD produces filled branches with
only era/GlobalTag changes.
