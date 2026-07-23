# CRAB production — customized NanoAOD (merged-electron IDs)

Produces the customized NanoAOD (with `Electron_mvaMergedElectron` + `Electron_mvaHDalitzMergedID*`)
from official MINIAOD, one CRAB task per sample. **Submit from lxplus** (needs `CRABClient` +
HTCondor; this cannot run on a plain worker node).

## One-time per session (lxplus)
```sh
# inside your CMSSW_15_0_X/src (or CMSSW_10_6_X/src) area, already built:
cmsenv
source /cvmfs/cms.cern.ch/common/crab-setup.sh

# proxy — either reuse the stored one, or (re)create it into that path:
voms-proxy-init --rfc --voms cms --valid 168:00 --out /eos/user/s/sqian/.proxy
export X509_USER_PROXY=/eos/user/s/sqian/.proxy

# data golden JSON (only needed if you submit the data sample):
export CND_GOLDEN_JSON=/cvmfs/cms-bril.cern.ch/cms-lumi-pog/CertificationFiles/... # official Legacy2018 JSON
```

## Submit
```sh
cd crab/
python crab_submit.py --release 15_0                 # all 15_0 samples (UL + Run3)
python crab_submit.py --release 10_6                 # all 10_6 samples (Run2 UL)
python crab_submit.py --only DYJetsToLL_M50_UL18     # a single sample
python crab_submit.py --release 15_0 --dryrun        # generate PSets only (no submit) — good first check
```
Run only the samples matching the release you built (`samples.py` tags each; Run3 → 15_0 only).

## Monitor
```sh
python crab_status.py status                 # all tasks
python crab_status.py status UL18            # tasks whose name contains 'UL18'
python crab_status.py resubmit               # resubmit failed jobs
python crab_status.py report                 # processed-lumi / eff (data)
```

## Config knobs (env vars, read by crab_submit.py)
| var | default | meaning |
|---|---|---|
| `X509_USER_PROXY` | `/eos/user/s/sqian/.proxy` | grid proxy |
| `CND_OUTLFN` | `/store/user/sqian/nanoDalitz` | output base LFN |
| `CND_SITE` | `T2_CH_CERN` | storage site |
| `CND_UNITS` | `2` | MINIAOD files per job (FileBased splitting) |
| `CND_GOLDEN_JSON` | — | lumimask for the data sample |

Output lands under `root://eoscms//eos/cms/store/user/sqian/nanoDalitz/<primaryDS>/<name>/…`.

## Samples (validated via DAS 2026-07-22)
| name | files | events | era |
|---|---|---|---|
| DYJetsToLL_M50_UL16APV | 980 | 91 M | Run2 2016preVFP |
| DYJetsToLL_M50_UL16 | 822 | 74 M | Run2 2016postVFP |
| DYJetsToLL_M50_UL17 | 3563 | 196 M | Run2 2017 |
| DYJetsToLL_M50_UL18 | 2465 | 196 M | Run2 2018 |
| EGamma_Run2018D_UL (data) | 10123 | 752 M | Run2 2018 |
| DYto2E_M50_Run3Summer22 | (DAS) | — | Run3 2022 |

These are DY tag/probe & data samples for a first pass; add signal (e.g. `GluGluHToZG`, low-mass
resonances) to `samples.py` the same way. Start small: `--only DYJetsToLL_M50_UL18` with a high
`CND_UNITS` for a quick end-to-end check before launching the full set.

## AN-21-053 (Higgs Dalitz, electron channel) sample list
`samples_AN21053.py` — the H→γ*γ→eeγ samples from CMS AN-21-053, DAS-resolved (117 total).

**Run2 = the full set to rerun the analysis** (`release="10_6"`, both merged-electron IDs):
- **Signal (EEG)**: all 6 modes GluGluH/VBFH/WH/ZH/**ttH/bbH** × M120/125/130 × UL16APV/16/17/18 = **72** (nominal TuneCP5).
- **Data**: DoubleEG+SingleElectron (2016/2017) + EGamma (2018), UL MiniAODv2 = **32**.
- **Background**: none — data-driven continuum fit (AN §2.3).

**Run3 = out-of-the-box ID test** (`release="15_0"`, HDalitz ID only — the ZprimeTo4l models are Run2-trained):
- **DY**: `DYto2E_M-50` powheg, Run3Summer22 pre/postEE = 2.
- **Data**: EGamma 2022 C–G + EGamma0/1 2023 B/C/D (22Sep2023 rereco) = 11.
- No Run3 Dalitz **signal** exists in DAS (the AN is Run2). 2024 is prompt-only — extend if wanted.
- Verified: the HDalitz merged-ID producer runs on Run3 MINIAOD unchanged (branches filled) — ID works out of the box.

Submit with `--samples` (release filter picks Run2 vs Run3):
```sh
python crab_submit.py --samples samples_AN21053 --release 10_6 --dryrun   # Run2 sanity (PSets only)
python crab_submit.py --samples samples_AN21053 --release 10_6            # all 104 Run2 (rerun set)
python crab_submit.py --samples samples_AN21053 --release 15_0            # all 13 Run3 (ID test)
python crab_submit.py --samples samples_AN21053 --only GluGluHToEEG_M125_UL18
```
Data needs the per-year/period golden JSON via `CND_GOLDEN_JSON`. Run2 runs
`customizeAllMergedElectron<year>` (both IDs); Run3 runs `customizeHDalitzMergedElectron` (HDalitz only).
