# customized_nano_dalitz

Custom **NanoAOD** producers that attach **merged-electron identification** to the
`Electron` table, for low-mass / boosted (Dalitz-like) e⁺e⁻ pairs that reconstruct as a
single `GsfElectron`. Two independent merged-electron IDs are provided side by side:

| Branch on the electron table | Origin | Runtime |
|---|---|---|
| `Electron_mvaMergedElectron` (+`_Category`) | [SanghyunKo/ZprimeTo4l](https://github.com/SanghyunKo/ZprimeTo4l) merged MVA | `GBRForest` (`CommonTools/MVAUtils`) |
| `Electron_mvaHDalitzMergedID` (+`_hdalitzMergedNGsf`, `_Category`, `_WPTight`) | [chw1207/HDalitzEle](https://github.com/chw1207/HDalitzEle) merged ID | **ONNXRuntime** (xgboost model) |

The HDalitz ID is XGBoost `multi:softprob` (Merged-1Gsf / Merged-2Gsf × EB/EE); the models
are shipped as ONNX so they run natively via `PhysicsTools/ONNXRuntime` in both releases.
The ONNX inference is **bit-identical** between the two branches and matches the original
xgboost c-API to float32 precision.

## Branches
| Branch | Release | Notes |
|---|---|---|
| `CMSSW_10_6_X` | 10.6.39 | Run2 UL, NanoAODv9. HDalitz via ONNXRuntime (no C++ xgboost in slc7). |
| `CMSSW_15_0_X` | 15.0.X | Run2 UL + **Run3 works for free**. ZprimeTo4l migrated to `esConsumes`; HDalitz backend-selectable (`onnx` default, `xgboost` optional). |

## Setup (CMSSW_15_0_X, native el9)
```sh
cmsrel CMSSW_15_0_20 && cd CMSSW_15_0_20/src && cmsenv && git cms-init
git cms-addpkg PhysicsTools/NanoAOD
git clone -b CMSSW_15_0_X https://github.com/DickyChant/customized_nano_dalitz .   # packages land in src/
scram b -j8
```
For **CMSSW_10_6_X**, `cmsrel CMSSW_10_6_39` (slc7 / `cmssw-el7` container on el8/9) and
`git clone -b CMSSW_10_6_X … .`.

## Run
```sh
cmsDriver.py nano_dalitz -s NANO --mc --era Run2_2018 \
  --conditions 106X_upgrade2018_realistic_v16 \
  --customise PhysicsTools/NanoDalitz/nano_cff.customizeAllMergedElectron \
  --filein file:DY_MiniAOD.root --fileout file:nano_dalitz.root -n 1000
```
Customise entry points (`PhysicsTools/NanoDalitz/nano_cff`):
- `customizeMergedElectron` / `customizeMergedElectron2016/2017/2018` — ZprimeTo4l ID only.
- `customizeHDalitzMergedElectron` — HDalitzEle ONNX ID only.
- `customizeAllMergedElectron` — both.

For Run3, use `--era Run3` and a Run3 GlobalTag (15_0 branch). The producers are era-agnostic;
the shipped HDalitz models are Run2-UL-trained, so Run3 scores run but are not Run3-calibrated
(retrain → `save_model` → `scripts/hdalitz_convert_onnx.py` → drop-in the new `.onnx`).

## Production at FNAL LPC (cmslpc)
Grid production is driven from `crab/` and is set up for **cmslpc**, native el9 — no container
needed for the 15_0 branch. Full instructions and tuning notes: **[`crab/README.md`](crab/README.md)**.

```sh
./scripts/build_lpc_150.sh          # one-time: CMSSW_15_0_20 area + packages (rsynced from this repo)
./crab/jsons/fetch.sh               # one-time: Run2 golden JSONs for the data lumimasks
cd crab/ && python3 crab_submit.py --samples samples_AN21053 --release 15_0 \
              --slim --nthreads 4 --units 8
```

Defaults worth knowing before a large submission:
- **Output site.** `CND_SITE` / `CND_OUTLFN` pick the storage element. Note `/store/user/sqian`
  on FNAL EOS is a *symlink to* `/store/user/sitianq` — one quota, ~2 TB, which the full
  AN-21-053 set (~7–10 TB) does **not** fit. Check quotas before submitting (see below).
- **`--slim` is effectively required** for the `_15X` twins and cuts ~24% (data) / ~16% (MC).
- **`--nthreads 4`** gives ~3.8x on the event loop for ~+900 MB; see `crab/README.md`.

## Models
Committed: the ONNX runtime models (`HDalitzEle/MergedID/data/*.onnx`) and the ZprimeTo4l
GBRForest weights (`ZprimeTo4l/MergedLepton/data/*.{xml,csv}`). The large xgboost-native
`.json` (used only for the optional `backend="xgboost"` cross-check on 15_0) are **not**
committed — regenerate from the original HDalitzEle `XGB_modelXGB.txt` if needed.

## Layout
`ZprimeTo4l/{ModifiedHEEP,MergedLepton}`, `PhysicsTools/NanoDalitz`, `HDalitzEle/MergedID`
(+ `Configuration/GenProduction` on 15_0). See `docs/` for the porting plans and `scripts/`
for build / smoke-test / model-conversion helpers, and `CLAUDE.md` for design notes.
