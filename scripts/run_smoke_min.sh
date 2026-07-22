#!/bin/bash
set -e
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
OV=/mnt/vdb/Codes/cmssw_dalitz/siteoverlay
export CMS_PATH="$OV"
cd /mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src && eval $(scram runtime -sh)
cd /mnt/vdb/Codes/cmssw_dalitz
echo "### cmsRun minimal electron-only smoke"
set +e
cmsRun smoke_min_cfg.py > cmsrun_min.log 2>&1
echo "### cmsRun RC=$?"
tail -15 cmsrun_min.log
set -e
echo "### validate"
python - <<'PY'
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
f = ROOT.TFile.Open("nanoDalitzMin.root"); assert f and not f.IsZombie(), "no output"
t = f.Get("Events"); brs = set(b.GetName() for b in t.GetListOfBranches())
for need in ("Electron_mvaMergedElectron", "Electron_mvaMergedElectronCategory"):
    assert need in brs, "MISSING %s" % need
    print("branch present:", need)
nev=t.GetEntries(); nele=0; nEBscore=0; cat={}; samp=[]
for i in range(nev):
    t.GetEntry(i); ne=t.nElectron
    if ne>0: nele+=1
    for j in range(ne):
        eta=t.Electron_eta[j]; pt=t.Electron_pt[j]
        sc=t.Electron_mvaMergedElectron[j]; c=int(t.Electron_mvaMergedElectronCategory[j])
        cat[c]=cat.get(c,0)+1
        if abs(eta)<1.479 and pt>20 and sc>0: nEBscore+=1
        if len(samp)<12 and pt>20: samp.append((pt,eta,sc,c))
print("events:",nev," with>=1 ele:",nele)
print("category counts:",cat)
print("barrel(pt>20) with score>0:",nEBscore)
print("sample (pt,eta,mergedMVA,cat):")
for pt,eta,sc,c in samp: print("   %6.1f  %+.3f  %.4f  %d"%(pt,eta,sc,c))
assert nele>0 and nEBscore>0, "no scored barrel electrons"
print("SMOKE_OK")
PY
