#!/usr/bin/env python
"""Multicrab submit for the customized-NanoAOD merged-electron ID production.

RUN ON cmslpc (FNAL LPC; needs CRABClient). This script:
  1) generates a per-sample cmsRun PSet via cmsDriver (with the NanoDalitz --customise), then
  2) submits one CRAB task per sample.

Usage (cmslpc, inside the CMSSW_X/src area after `cmsenv`):
    source /cvmfs/cms.cern.ch/common/crab-setup.sh
    voms-proxy-init --rfc --voms cms --valid 168:00      # default proxy path is fine on LPC
    python3 crab_submit.py --release 15_0                # submit all 15_0 samples
    python3 crab_submit.py --only DYJetsToLL_M50_UL18    # a single sample
    python3 crab_submit.py --release 15_0 --dryrun       # just generate PSets, don't submit
"""
import argparse, importlib, os, subprocess, sys

PROXY = os.environ.get("X509_USER_PROXY", "/uscms/home/sitianq/x509up_u25265")
# NOTE: CRAB requires /store/user/<CERN username> (sqian), not the FNAL one (sitianq);
# on FNAL EOS the corresponding area is /eos/uscms/store/user/sqian.
OUT_LFN_BASE = os.environ.get("CND_OUTLFN", "/store/user/sqian/nanoDalitz")
STORAGE_SITE = os.environ.get("CND_SITE", "T3_US_FNALLPC")
UNITS_PER_JOB = int(os.environ.get("CND_UNITS", "2"))     # MINIAOD files per job
NTHREADS = int(os.environ.get("CND_THREADS", "1"))        # cmsRun threads == CRAB numCores

# Memory request = max(what the job needs, what the slot gives you anyway).
#
#   need: measured with scripts/bench_threads.sh -- ~2.6 GB single-threaded, +~305 MB per added
#         thread (conditions, geometry and the ParticleNet/GBRForest models are per-process).
#   floor: a grid slot is carved at >= 2 GB per core, so an N-core slot always carries >= N*2 GB.
#         Requesting less than that buys no extra matching flexibility -- it is free headroom.
#
# Requesting *more* than N*2000 is what narrows matching (it excludes minimal slots), so the
# per-core term is 2000, not 2500.
MEM_FLOOR_MB = int(os.environ.get("CND_MEM_FLOOR", "4000"))                 # 1-thread need
MEM_PER_EXTRA_THREAD_MB = int(os.environ.get("CND_MEM_PER_THREAD", "500"))  # measured ~305 + headroom
MEM_PER_CORE_MIN_MB = int(os.environ.get("CND_MEM_PER_CORE_MIN", "2000"))   # minimal grid slot


def job_memory_mb(nthreads):
    need = MEM_FLOOR_MB + (nthreads - 1) * MEM_PER_EXTRA_THREAD_MB
    return max(need, nthreads * MEM_PER_CORE_MIN_MB)

# UL/Legacy golden JSONs, per year (fetched into jsons/ by jsons/fetch.sh).
# A GOLDEN* lumimask tag in the sample list resolves here by the sample's era;
# CND_GOLDEN_JSON (if set) overrides everything.
CRABDIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_JSONS = {
    "2016": os.path.join(CRABDIR, "jsons", "Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"),
    "2017": os.path.join(CRABDIR, "jsons", "Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt"),
    "2018": os.path.join(CRABDIR, "jsons", "Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"),
}


def golden_json(s):
    override = os.environ.get("CND_GOLDEN_JSON")
    if override:
        return override
    for year, path in GOLDEN_JSONS.items():
        if year in s["era"]:
            if not os.path.exists(path):
                sys.exit("golden JSON missing: %s (run jsons/fetch.sh)" % path)
            return path
    sys.exit("no golden JSON for era %r (set CND_GOLDEN_JSON)" % s["era"])


SLIM_CUSTOMISE = "PhysicsTools/NanoDalitz/nano_cff.slimNanoDalitz"


def make_pset(s, slim=False, nthreads=1):
    pset = "pset_%s.py" % s["name"]
    tier = "NANOAOD" if s["isData"] else "NANOAODSIM"
    customise = s["customise"]
    if slim:                       # append the H->eeg output-slimming customise (drops
        customise += "," + SLIM_CUSTOMISE   # LowPtElectron/Proton-PPS/IsoTrack/SoftActivity/AK8)
    cmd = ["cmsDriver.py", "nanoDalitz_%s" % s["name"], "-s", "NANO",
           "--data" if s["isData"] else "--mc",
           "--era", s["era"], "--conditions", s["globaltag"],
           "--customise", customise,
           "--eventcontent", tier, "--datatier", tier,
           "--filein", "file:dummy.root", "--fileout", "file:nano.root",
           "--nThreads", str(nthreads),
           "-n", "-1", "--no_exec", "--python_filename", pset]
    print("[pset]", " ".join(cmd))
    subprocess.check_call(cmd)
    return pset


def submit(s, dryrun, slim=False, nthreads=1, units=None):
    pset = make_pset(s, slim=slim, nthreads=nthreads)
    if dryrun:
        print("[dryrun] PSet ready:", pset, "\n"); return
    from CRABClient.UserUtilities import config
    from CRABAPI.RawCommand import crabCommand
    c = config()
    c.General.requestName = ("nanoDalitz_%s" % s["name"])[:100]
    c.General.workArea = "crab_projects"
    c.General.transferOutputs = True
    c.General.transferLogs = False
    c.JobType.pluginName = "Analysis"
    c.JobType.psetName = pset
    # the _15X nano chain peaks at ~3.5 GB even single-threaded (2500 -> jobs killed, 50660)
    c.JobType.maxMemoryMB = job_memory_mb(nthreads)
    c.JobType.numCores = nthreads
    c.Data.inputDataset = s["dataset"]
    c.Data.inputDBS = "global"
    c.Data.splitting = "FileBased"
    c.Data.unitsPerJob = units or UNITS_PER_JOB
    c.Data.outLFNDirBase = OUT_LFN_BASE
    c.Data.publication = False
    c.Data.outputDatasetTag = s["name"]
    if s["isData"] and s.get("lumimask"):
        lm = s["lumimask"]
        # placeholder tags (GOLDEN_UL / GOLDEN_2018 / ...) resolve per-era from jsons/
        # (or CND_GOLDEN_JSON if set); a real path in lumimask is used as-is.
        c.Data.lumiMask = golden_json(s) if lm.startswith("GOLDEN") else lm
    c.Site.storageSite = STORAGE_SITE
    print("[submit]", c.General.requestName, "->", s["dataset"])
    # CRABClient can only submit once per process (state pollution: the 2nd+ call fails
    # with an empty error) -> fork each submit, per the official multicrab recipe.
    from multiprocessing import Process
    p = Process(target=crabCommand, args=("submit",), kwargs=dict(config=c))
    p.start(); p.join()
    if p.exitcode != 0:
        print("[submit-FAILED]", c.General.requestName, "(exit %s)" % p.exitcode)
        return c.General.requestName
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", default="samples", help="sample module to import (e.g. samples_AN21053)")
    ap.add_argument("--release", choices=["10_6", "15_0"], help="only submit samples for this release")
    ap.add_argument("--only", nargs="*", default=[], help="submit only these sample name(s)")
    ap.add_argument("--dryrun", action="store_true", help="generate PSets only, do not submit")
    ap.add_argument("--slim", action="store_true",
                    help="append slimNanoDalitz (drop LowPtElectron/Proton-PPS/IsoTrack/SoftActivity/AK8) "
                         "-> ~23%% smaller data, ~15%% smaller MC")
    ap.add_argument("--nthreads", type=int, default=NTHREADS,
                    help=("cmsRun threads == CRAB numCores (default %d). Memory is sized from "
                          "measurement: %d MB + %d MB per extra thread."
                          % (NTHREADS, MEM_FLOOR_MB, MEM_PER_EXTRA_THREAD_MB)))
    ap.add_argument("--units", type=int, default=None,
                    help=("MINIAOD files per job (default %d); raise it with --nthreads so job "
                          "runtime stays well above the ~2 min startup cost" % UNITS_PER_JOB))
    a = ap.parse_args()
    os.environ.setdefault("X509_USER_PROXY", PROXY)
    SAMPLES = importlib.import_module(a.samples).SAMPLES
    print("samples module:", a.samples, "(%d entries)" % len(SAMPLES))
    picked = [s for s in SAMPLES
              if (not a.release or s["release"] == a.release)
              and (not a.only or s["name"] in a.only)]
    if not picked:
        sys.exit("no samples matched (release=%s only=%s)" % (a.release, a.only))
    print("proxy:", os.environ["X509_USER_PROXY"], "| out:", OUT_LFN_BASE, "| site:", STORAGE_SITE,
          "| slim:", a.slim, "| threads:", a.nthreads,
          "| mem:", job_memory_mb(a.nthreads), "MB",
          "| units/job:", a.units or UNITS_PER_JOB)
    print("samples:", [s["name"] for s in picked], "\n")
    failed = [f for f in (submit(s, a.dryrun, slim=a.slim, nthreads=a.nthreads, units=a.units)
                          for s in picked) if f]
    if failed:
        sys.exit("FAILED submits (%d): %s" % (len(failed), " ".join(failed)))
    print("all %d task(s) submitted OK" % len(picked))


if __name__ == "__main__":
    main()
