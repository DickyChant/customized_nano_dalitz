#!/bin/bash
# Smoke-test the 15_0 build on the SAME UL2018 MC MINIAOD staged on /eos/cms/store
# (tests both the port AND 10_6-MINIAOD -> 15_0 read compatibility).
set -e
export SCRAM_ARCH=el9_amd64_gcc12
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz_150/CMSSW_15_0_20/src && eval $(scram runtime -sh)
export SITECONFIG_PATH=/cvmfs/cms.cern.ch/SITECONF/T2_CH_CERN   # 15_0 uses this for site-local-config
scram b -j4 python >/dev/null 2>&1
cd /mnt/vdb/Codes/cmssw_dalitz_150
# reuse the identical minimal electron-only cfg (same EOS input, UL18 MC GT)
cp /mnt/vdb/Codes/cmssw_dalitz/smoke_min_cfg.py ./smoke_min_cfg.py
echo "### cmsRun (15_0) minimal electron-only smoke over /eos/cms/store MC MINIAOD"
set +e
cmsRun smoke_min_cfg.py > cmsrun_min_150.log 2>&1
echo "### cmsRun RC=$?"
grep -iE 'Successfully opened|Fatal|Exception|Error' cmsrun_min_150.log | head -8
set -e
echo "### validate"
python3 - <<'PY'
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
f = ROOT.TFile.Open("nanoDalitzMin.root"); assert f and not f.IsZombie(), "no output"
t = f.Get("Events"); brs = set(b.GetName() for b in t.GetListOfBranches())
for need in ("Electron_mvaMergedElectron", "Electron_mvaMergedElectronCategory"):
    assert need in brs, "MISSING %s" % need
    print("branch present:", need)
nev=t.GetEntries(); nele=0; nEB=0; cat={}; samp=[]
for i in range(nev):
    t.GetEntry(i); ne=t.nElectron
    if ne>0: nele+=1
    for j in range(ne):
        eta=t.Electron_eta[j]; pt=t.Electron_pt[j]
        sc=t.Electron_mvaMergedElectron[j]; c=int(t.Electron_mvaMergedElectronCategory[j])
        cat[c]=cat.get(c,0)+1
        if abs(eta)<1.479 and pt>20 and sc>0: nEB+=1
        if len(samp)<12 and pt>20: samp.append((pt,eta,sc,c))
print("events:",nev," with>=1 ele:",nele)
print("category counts:",cat)
print("barrel(pt>20) with score>0:",nEB)
print("sample (pt,eta,mergedMVA,cat):")
for pt,eta,sc,c in samp: print("   %6.1f  %+.3f  %.4f  %d"%(pt,eta,sc,c))
assert nele>0, "no electrons"
print("SMOKE_OK_150" if nEB>0 else "BRANCHES_PRESENT_no_scored_barrel")
PY
