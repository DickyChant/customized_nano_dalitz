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

**Run2 also via CMSSW_15_0_X** (`_15X` twins of every Run2 entry, `release="15_0"`): same UL dataset,
GT and `customizeAllMergedElectron<year>` (both IDs), and the **same era incl. `run2_nanoAOD_106Xv2`**.
That modifier is required: native v15 nano over UL MiniAOD aborts (`pvbsTable` wants
`offlineSlimmedPrimaryVerticesWithBS`, absent in UL MiniAODv2). So a `_15X` job produces the same
106Xv2-schema nano as the 10_6 path, just from the newer release.
> ⚠️ **The `_15X` twins require `--slim`.** Under the 106Xv2 modifier the boostedTau `againstEle` MVA6
> discriminant runs (via `linkedObjects`) and asks for a GBRForest the UL conditions ship under a
> different label → `NoProductResolverException`. `--slim` drops boostedTau (and detaches
> `linkedObjects.boostedTaus`), which removes that chain — so a `_15X --slim` job runs clean end-to-end
> over UL MiniAOD (validated: ttH_M125 UL18, 100 ev, RC=0). Without `--slim` the twins crash. Note they
> still duplicate the 10_6 content and double the ~9 TB data volume, so weigh whether to submit them at
> all (the clean split is Run2→10_6, Run3→15_0).

Submit with `--samples` (release filter picks the CMSSW build — build that release's area first):
```sh
python crab_submit.py --samples samples_AN21053 --release 10_6 --dryrun   # Run2 sanity (PSets only)
python crab_submit.py --samples samples_AN21053 --release 10_6            # 104 Run2 via 10_6 (native)
python crab_submit.py --samples samples_AN21053 --release 15_0            # 104 Run2 (_15X) + 13 Run3
python crab_submit.py --samples samples_AN21053 --only GluGluHToEEG_M125_UL18_15X
```
Data needs the per-year/period golden JSON via `CND_GOLDEN_JSON` (any `GOLDEN*` lumimask tag is
resolved from it). Run2 runs `customizeAllMergedElectron<year>` (both IDs); Run3 runs
`customizeHDalitzMergedElectron` (HDalitz only). **221 entries**: 104 Run2·10_6 + 104 Run2·15X + 13 Run3.

## Output slimming — `--slim` (recommended default)
Add `--slim` to any submit to append `nano_cff.slimNanoDalitz`, which drops nano tables with no role
in H→eeγ. **Kept** (per analysis): Jet(AK4), Electron(+merged IDs), Photon, Muon, **Tau, CorrT1METJet,
MET/PuppiMET/DeepMET**, SV, PV, trigger, gen. **Dropped**: **boostedTau**, LowPtElectron, Proton/PPS
(`protonTable`+`multiRP`/`singleRP`), IsoTrack, SoftActivityJet (`saJetTable`/`saTable`),
FatJet/SubJet/AK8 (+ their gen/MC/constituent tables) — 20 table producers; their upstream producers
(incl. the heavy AK8 ParticleNet/DeepBoosted taggers, and the whole boostedTau discriminant chain via
the detached `linkedObjects.boostedTaus`) go unscheduled, so it also saves CPU.
```sh
python crab_submit.py --samples samples_AN21053 --release 10_6 --slim         # slimmed Run2
python crab_submit.py --samples samples_AN21053 --release 15_0 --slim --dryrun # inspect slimmed PSet
```
Savings (measured from the official NanoAODv9 per-collection breakdown): **~24% smaller data files,
~16% smaller MC**. Since the production is ~92% data bytes, that's **~2.5–3 TB off the ~9.8 TB total**.
Nothing physics-relevant to the channel is removed — run it by default (and it is **required** for the
`_15X` twins, which otherwise crash on the boostedTau ES).
