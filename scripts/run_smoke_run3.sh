#!/bin/bash
export SCRAM_ARCH=el9_amd64_gcc12
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz_150/CMSSW_15_0_20/src && eval $(scram runtime -sh)
export SITECONFIG_PATH=/cvmfs/cms.cern.ch/SITECONF/T2_CH_CERN
scram b -j2 python >/dev/null 2>&1
cd /mnt/vdb/Codes/cmssw_dalitz_150
echo "### cmsRun HDalitz merged-ID smoke (15_0)"
( while true; do ps -o rss= -C cmsRun 2>/dev/null | awk '{s+=$1} END{if(s)print "  RSS(cmsRun) MB:", int(s/1024)}'; sleep 8; done ) &
MON=$!
cmsRun smoke_hdalitz_run3_cfg.py > cmsrun_run3.log 2>&1; RC=$?
kill $MON 2>/dev/null
echo "### cmsRun RC=$RC"
grep -iE 'Fatal|Exception|Error|feature size|xgboost' cmsrun_run3.log | head -8
echo "### validate"
python3 - <<'PY'
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
f=ROOT.TFile.Open("nanoHDalitzRun3.root"); assert f and not f.IsZombie(),"no output"
t=f.Get("Events"); brs=set(b.GetName() for b in t.GetListOfBranches())
for n in ("Electron_mvaHDalitzMergedID","Electron_hdalitzMergedNGsf","Electron_hdalitzMergedCategory","Electron_hdalitzMergedWPTight"):
    assert n in brs, "MISSING "+n
    print("branch present:", n)
nev=t.GetEntries(); nele=0; ncat={}; samp=[]
for i in range(nev):
    t.GetEntry(i); ne=t.nElectron
    if ne>0: nele+=1
    for j in range(ne):
        c=int(t.Electron_hdalitzMergedCategory[j]); ncat[c]=ncat.get(c,0)+1
        if len(samp)<15:
            samp.append((t.Electron_pt[j], t.Electron_eta[j], t.Electron_mvaHDalitzMergedID[j],
                         int(t.Electron_hdalitzMergedNGsf[j]), c, int(t.Electron_hdalitzMergedWPTight[j])))
print("events:",nev," with>=1 ele:",nele)
print("category counts (0 M1EB,1 M1EE,2 M2EB,3 M2EE):",ncat)
print("sample (pt, eta, HDalitzScore, nGsf, cat, WPtight):")
for s in samp: print("   %6.1f  %+.3f  %.4f  ngsf=%d cat=%d wp=%d"%s)
assert nele>0,"no electrons"
print("HDALITZ_RUN3_OK")
PY
