#!/usr/bin/env python
"""Multicrab submit for the customized-NanoAOD merged-electron ID production.

RUN ON lxplus (needs CRABClient + HTCondor). This script:
  1) generates a per-sample cmsRun PSet via cmsDriver (with the NanoDalitz --customise), then
  2) submits one CRAB task per sample.

Usage (lxplus, inside the CMSSW_X/src area after `cmsenv`):
    source /cvmfs/cms.cern.ch/common/crab-setup.sh
    export X509_USER_PROXY=/eos/user/s/sqian/.proxy      # or: voms-proxy-init --rfc --voms cms --valid 168:00 --out /eos/user/s/sqian/.proxy
    python crab_submit.py --release 15_0                 # submit all 15_0 samples
    python crab_submit.py --only DYJetsToLL_M50_UL18     # a single sample
    python crab_submit.py --release 10_6 --dryrun        # just generate PSets, don't submit
"""
import argparse, importlib, os, subprocess, sys

PROXY = os.environ.get("X509_USER_PROXY", "/eos/user/s/sqian/.proxy")
OUT_LFN_BASE = os.environ.get("CND_OUTLFN", "/store/user/sqian/nanoDalitz")
STORAGE_SITE = os.environ.get("CND_SITE", "T2_CH_CERN")
UNITS_PER_JOB = int(os.environ.get("CND_UNITS", "2"))     # MINIAOD files per job


SLIM_CUSTOMISE = "PhysicsTools/NanoDalitz/nano_cff.slimNanoDalitz"


def make_pset(s, slim=False):
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
           "-n", "-1", "--no_exec", "--python_filename", pset]
    print("[pset]", " ".join(cmd))
    subprocess.check_call(cmd)
    return pset


def submit(s, dryrun, slim=False):
    pset = make_pset(s, slim=slim)
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
    c.JobType.maxMemoryMB = 2500
    c.JobType.numCores = 1
    c.Data.inputDataset = s["dataset"]
    c.Data.inputDBS = "global"
    c.Data.splitting = "FileBased"
    c.Data.unitsPerJob = UNITS_PER_JOB
    c.Data.outLFNDirBase = OUT_LFN_BASE
    c.Data.publication = False
    c.Data.outputDatasetTag = s["name"]
    if s["isData"] and s.get("lumimask"):
        lm = s["lumimask"]
        # placeholder tags (GOLDEN_UL / GOLDEN_2018 / ...) are resolved from CND_GOLDEN_JSON;
        # a real path in lumimask is used as-is.
        c.Data.lumiMask = os.environ.get("CND_GOLDEN_JSON", lm) if lm.startswith("GOLDEN") else lm
    c.Site.storageSite = STORAGE_SITE
    print("[submit]", c.General.requestName, "->", s["dataset"])
    crabCommand("submit", config=c)
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
          "| slim:", a.slim)
    print("samples:", [s["name"] for s in picked], "\n")
    for s in picked:
        submit(s, a.dryrun, slim=a.slim)


if __name__ == "__main__":
    main()
