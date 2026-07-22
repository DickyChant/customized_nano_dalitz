#!/bin/bash
# Event-level smoke test over REAL Run2017 UL DATA MINIAOD (DoubleEG Run2017D, 09Aug2019_UL2017
# di-electron skim), staged on CERN EOS disk, kerberos-readable. No grid proxy needed.
set -e
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src
eval $(scram runtime -sh)

# CMS_PATH overlay providing a valid SITECONF/local (missing on this host)
OV=/mnt/vdb/Codes/cmssw_dalitz/siteoverlay
if [ ! -e "$OV/SITECONF/local/JobConfig/site-local-config.xml" ]; then
  rm -rf "$OV"; mkdir -p "$OV"
  for d in /cvmfs/cms.cern.ch/*; do ln -sfn "$d" "$OV/$(basename "$d")"; done
  rm -f "$OV/SITECONF"; mkdir -p "$OV/SITECONF"
  for d in /cvmfs/cms.cern.ch/SITECONF/*; do ln -sfn "$d" "$OV/SITECONF/$(basename "$d")"; done
  ln -sfn /cvmfs/cms.cern.ch/SITECONF/T2_CH_CERN "$OV/SITECONF/local"
fi
export CMS_PATH="$OV"

INFILE='root://eoscms.cern.ch//eos/cms/store/group/phys_egamma/CMSDAS2020/MiniAOD/DiEleSkim/data/DoubleEG__Run2017D__09Aug2019_UL2017-v1__DiEleSkimSS_1.root'
NEV=${1:-300}

cd /mnt/vdb/Codes/cmssw_dalitz
echo "### cmsDriver NANO (Run2017 UL DATA, DoubleEG) over $NEV events"
cmsDriver.py nanoDalitzData -s NANO --data --eventcontent NANOAOD --datatier NANOAOD \
  --era Run2_2017,run2_nanoAOD_106Xv2 --conditions 106X_dataRun2_v35 \
  --customise PhysicsTools/NanoDalitz/nano_cff.customizeMergedElectron2017NoMET \
  --filein "$INFILE" --fileout file:nanoDalitzData.root -n $NEV --no_exec \
  --python_filename nanoDalitzData_cfg.py 2>&1 | tail -3
echo "### cmsRun"
set +e
cmsRun nanoDalitzData_cfg.py > cmsrun_data.log 2>&1
echo "### cmsRun RC=$?"
tail -20 cmsrun_data.log
set -e

echo "### validate branches"
python - <<'PY'
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
f = ROOT.TFile.Open("nanoDalitzData.root")
assert f and not f.IsZombie(), "output root file missing/zombie"
t = f.Get("Events")
brs = set(b.GetName() for b in t.GetListOfBranches())
for need in ("Electron_mvaMergedElectron", "Electron_mvaMergedElectronCategory"):
    assert need in brs, "MISSING branch %s" % need
    print("branch present:", need)
nev = t.GetEntries()
n_ele_ev = 0; n_eb_scored = 0; cat = {}
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
        if len(samples) < 12 and pt > 20:
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
