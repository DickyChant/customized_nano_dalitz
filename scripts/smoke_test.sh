#!/bin/bash
# Event-level smoke test over a physically-present, kerberos-readable UL18 MINIAOD
# (egamma group sample; PAT step = CMSSW_10_6_25, UL2018). No grid proxy needed.
set -e
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src
eval $(scram runtime -sh)

# --- CMS_PATH overlay: mirror cvmfs but provide a valid SITECONF/local (missing on this host) ---
OV=/mnt/vdb/Codes/cmssw_dalitz/siteoverlay
if [ ! -e "$OV/SITECONF/local/JobConfig/site-local-config.xml" ]; then
  rm -rf "$OV"; mkdir -p "$OV"
  for d in /cvmfs/cms.cern.ch/*; do ln -sfn "$d" "$OV/$(basename "$d")"; done  # SITECONF becomes a symlink
  rm -f "$OV/SITECONF"; mkdir -p "$OV/SITECONF"                                # replace with a real dir
  for d in /cvmfs/cms.cern.ch/SITECONF/*; do ln -sfn "$d" "$OV/SITECONF/$(basename "$d")"; done
  ln -sfn /cvmfs/cms.cern.ch/SITECONF/T2_CH_CERN "$OV/SITECONF/local"
fi
export CMS_PATH="$OV"
echo "### CMS_PATH=$CMS_PATH ; site-local-config:"; ls -l "$OV/SITECONF/local/JobConfig/site-local-config.xml"

# RunIISummer20UL17 DY MINIAODv2 (central dataset, streamed via AAA — needs a grid proxy).
export X509_USER_PROXY=${X509_USER_PROXY:-/mnt/vdb/Codes/cmssw_dalitz/x509up}
voms-proxy-info -exists -valid 0:10 2>/dev/null || { echo "NO_VALID_PROXY at $X509_USER_PROXY"; exit 3; }
DATASET='/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/MINIAODSIM'
LFN=$(dasgoclient -query="file dataset=$DATASET" 2>/dev/null | sort | head -1)
[ -z "$LFN" ] && { echo "DAS_EMPTY for $DATASET"; exit 4; }
INFILE="root://cms-xrd-global.cern.ch/$LFN"
echo "### input: $INFILE"
NEV=${1:-300}

cd /mnt/vdb/Codes/cmssw_dalitz
echo "### cmsDriver NANO (UL17 DY->ee) over $NEV events"
cmsDriver.py nanoDalitzSmoke -s NANO --mc --eventcontent NANOAODSIM --datatier NANOAODSIM \
  --era Run2_2017,run2_nanoAOD_106Xv2 --conditions 106X_mc2017_realistic_v9 \
  --customise PhysicsTools/NanoDalitz/nano_cff.customizeMergedElectron2017 \
  --filein "$INFILE" --fileout file:nanoDalitzSmoke.root -n $NEV --no_exec \
  --python_filename nanoDalitzSmoke_cfg.py 2>&1 | tail -3
echo "### cmsRun"
set +e
cmsRun nanoDalitzSmoke_cfg.py > cmsrun.log 2>&1
echo "### cmsRun RC=$?"
tail -18 cmsrun.log
set -e

echo "### validate branches (python2 / ROOT 6.14 safe)"
python - <<'PY'
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
f = ROOT.TFile.Open("nanoDalitzSmoke.root")
assert f and not f.IsZombie(), "output root file missing/zombie"
t = f.Get("Events")
brs = set(b.GetName() for b in t.GetListOfBranches())
for need in ("Electron_mvaMergedElectron", "Electron_mvaMergedElectronCategory"):
    assert need in brs, "MISSING branch %s" % need
    print("branch present:", need)

nev = t.GetEntries()
n_ele_ev = 0; n_eb_scored = 0; cat = {-1:0,0:0,1:0,2:0}
samples = []
for i in range(nev):
    t.GetEntry(i)
    ne = t.nElectron
    if ne > 0: n_ele_ev += 1
    for j in range(ne):
        eta = t.Electron_eta[j]; pt = t.Electron_pt[j]
        sc = t.Electron_mvaMergedElectron[j]; c = int(t.Electron_mvaMergedElectronCategory[j])
        cat[c] = cat.get(c,0)+1
        if abs(eta) < 1.479 and pt > 20 and sc > 0: n_eb_scored += 1
        if len(samples) < 10 and pt > 15:
            samples.append((pt,eta,sc,c))
print("events:", nev, " with >=1 electron:", n_ele_ev)
print("category counts:", cat)
print("barrel(pt>20) electrons with score>0:", n_eb_scored)
print("sample (pt, eta, mergedMVA, cat):")
for pt,eta,sc,c in samples:
    print("   %6.1f  %+.3f  %.4f  %d" % (pt,eta,sc,c))
assert n_ele_ev > 0, "no electrons at all"
print("SMOKE_OK")
PY
