# CRAB production — customized NanoAOD (merged-electron IDs)

Produces the customized NanoAOD (with `Electron_mvaMergedElectron` + `Electron_mvaHDalitzMergedID*`)
from official MINIAOD, one CRAB task per sample. **Submit from cmslpc** (FNAL LPC; needs
`CRABClient`; this cannot run on a plain worker node).

## One-time setup (cmslpc)
```sh
# build the CMSSW area (el9 native, CMSSW_15_0_20) — one time:
./scripts/build_lpc_150.sh          # creates /uscms_data/d3/sitianq/nu_dalitz/CMSSW_15_0_20

# fetch the Run2 golden JSONs (data lumimasks resolve from here automatically):
./crab/jsons/fetch.sh
```

## Per session (cmslpc)
```sh
cd /uscms_data/d3/sitianq/nu_dalitz/CMSSW_15_0_20/src && cmsenv
source /cvmfs/cms.cern.ch/common/crab-setup.sh

# proxy (default location is fine on LPC):
voms-proxy-init --rfc --voms cms --valid 168:00
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
| `X509_USER_PROXY` | `/uscms/home/sitianq/x509up_u25265` | grid proxy |
| `CND_OUTLFN` | `/store/user/sqian/nanoDalitz` | output base LFN (CRAB wants the **CERN** username) |
| `CND_SITE` | `T3_US_FNALLPC` | storage site |
| `CND_UNITS` | `2` | MINIAOD files per job (FileBased splitting); `--units` overrides |
| `CND_THREADS` | `1` | cmsRun threads == CRAB `numCores`; `--nthreads` overrides |
| `CND_MEM_FLOOR` | `4000` | 1-thread memory need (the chain peaks at ~3.5 GB) |
| `CND_MEM_PER_THREAD` | `500` | added need per extra thread (measured ~305 + headroom) |
| `CND_MEM_PER_CORE_MIN` | `2000` | minimal grid slot per core — the request never goes below `N * this` |
| `CND_GOLDEN_JSON` | — | override lumimask (default: per-era JSON from `jsons/`) |

Output lands under `root://cmseos.fnal.gov//store/user/sqian/nanoDalitz/<primaryDS>/<name>/…`.
Data lumimasks resolve automatically: a `GOLDEN*` tag picks the per-era UL golden JSON from
`crab/jsons/` (run `jsons/fetch.sh` once); `CND_GOLDEN_JSON` overrides if set.

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
Data lumimasks (`GOLDEN*` tags) resolve automatically from `crab/jsons/` per era
(`CND_GOLDEN_JSON` overrides). Run2 runs `customizeAllMergedElectron<year>` (both IDs); Run3 runs
`customizeHDalitzMergedElectron` (HDalitz only). **221 entries**: 104 Run2·10_6 + 104 Run2·15X + 13 Run3.

## Multithreading — `--nthreads` (recommended for the remaining production)

`--nthreads N` sets both `cmsDriver --nThreads N` and CRAB `numCores = N`, and sizes the memory
request as **`max(measured need, N * 2000 MB)`**: a grid slot is carved at >= 2 GB per core, so an
N-core slot carries >= N*2 GB whether you ask for it or not — requesting less buys nothing, while
requesting *more* than N*2000 excludes minimal slots and narrows matching.

| threads | request | MB/core |
|---|---|---|
| 1 | 4000 | 4000 |
| 2 | 4500 | 2250 |
| 4 | 8000 | 2000 |

Measured on `GluGluHToEEG_M125_UL18` MINIAOD (15956 ev/file, 300-event runs, `scripts/bench_threads.sh`):

| threads | s/event | speedup | min per file | peak RSS | RSS per core |
|---|---|---|---|---|---|
| 1 | 0.186 | 1.00x | 49 | 2560 MB | 2560 |
| 2 | 0.090 | 2.06x | 24 | 2861 MB | 1430 |
| 4 | 0.048 | 3.83x | 13 | 3475 MB | 868 |

The event loop scales ~linearly (3.8x on 4 threads) while memory grows only ~305 MB per added
thread — conditions, geometry and the ParticleNet/GBRForest models are per-process, not per-thread.
So RSS *per core* falls from 2560 MB to 868 MB going 1 -> 4 threads.

**Why this matters more than speed:** a 1-core job needing ~3.5-4 GB asks for more than the
2500 MB/core the grid guarantees, so CRAB warns and jobs sit idle waiting for a matching slot
(seen on the first batch). The same job as 2 cores / 5000 MB fits inside the guarantee and matches
normally.

Not parallelized: a fixed **~3 min startup** (job start to 1st record; almost pure I/O wait on
Frontier conditions + CVMFS, only ~14 s of CPU) plus ~18 s on the first event. That cost is per
*job*, so pair `--nthreads` with a larger `--units` to amortize it.

Recommended for the remaining Run2 set (~1.8 h/job, ~3.5-4.5 GB inside a 4x2500 MB request):
```sh
python3 crab_submit.py --samples samples_AN21053 --release 15_0 --slim --nthreads 4 --units 8
```
Note `numCores` cannot be changed by `crab resubmit` — it is fixed at submission, so switching an
existing task to multicore means killing it and submitting a new one.

## Storage — check quota BEFORE a large submission
The full AN-21-053 set is ~7-10 TB even slimmed. Check where it can actually land:

```sh
# FNAL EOS quota (charged to the unix account; /store/user/sqian is a SYMLINK to /store/user/sitianq)
eos root://cmseos.fnal.gov quota /eos/uscms/store/user/$USER

# LPC nobackup + home
quota -s                                  # /uscms_data/d3 (nobackup) and /uscms/home

# IHEP (T2_CN_Beijing). gfal-xattr returns no quota data on this endpoint, so use a
# WebDAV PROPFIND for the RFC 4331 properties:
gfal-ls -l https://cceos.ihep.ac.cn:9000/eos/ihep/cms/store/user/sqian
curl -s --capath /etc/grid-security/certificates --cert $X509_USER_PROXY --key $X509_USER_PROXY \
  -X PROPFIND -H "Depth: 0" \
  --data '<?xml version="1.0"?><D:propfind xmlns:D="DAV:"><D:prop><D:quota-available-bytes/><D:quota-used-bytes/></D:prop></D:propfind>' \
  https://cceos.ihep.ac.cn:9000/eos/ihep/cms/store/user/sqian
```

Measured 2026-08-29: **LPC EOS 1.85/2.00 TB logical (92%, warning)** vs **IHEP 5.99 TB used,
509 TB available**. For a full-set production, submit to IHEP:
```sh
export CND_SITE=T2_CN_Beijing
export CND_OUTLFN=/store/user/sqian/nanoDalitz
```
Site endpoints come from `/cvmfs/cms.cern.ch/SITECONF/<site>/storage.json`.

Put big test inputs / throwaway outputs in the LPC 3-day scratch, **not** the project area:
`/uscmst1b_scratch/lpc1/3DayLifetime/$USER/` (`scripts/bench_threads.sh` already defaults there).

## Gotchas seen in production
- **Jobs killed with exit 50660** = HTCondor memory kill. The chain needs ~3.3-4.3 GB on the
  grid; `maxMemoryMB` is sized by `job_memory_mb()` (see the multithreading section). A job
  killed this way reports `N used vs. M requested` in `crab status --verboseErrors`.
- **`crab resubmit` cannot change `numCores`** (only maxmemory / maxjobruntime / priority), and
  it only touches *failed* jobs — it cannot re-request memory for idle ones. Switching a task to
  multicore, or fixing memory on jobs that have not failed, means kill + resubmit.
- **CRABClient can only submit once per process**: the 2nd and later `crabCommand("submit")`
  calls fail with an *empty* exception. `crab_submit.py` forks each submit into its own
  `multiprocessing.Process` (the official multicrab recipe). One failed submit no longer aborts
  the batch; failures are listed at the end.
- **Idle jobs are usually data locality, not memory.** 53 of the 72 Run2 signal datasets have a
  single disk replica, so a task can only run at one site and waits for capacity there. Check
  with `dasgoclient -query="site dataset=<DS>"` before assuming a config problem; the lever is
  `Data.ignoreLocality`, not more memory.
- Killed/superseded CRAB project dirs can be parked in the 3DayLifetime scratch instead of
  deleted, so the logs survive a few days.

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
