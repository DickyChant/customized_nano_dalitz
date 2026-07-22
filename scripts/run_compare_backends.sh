#!/bin/bash
export SCRAM_ARCH=el9_amd64_gcc12
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz_150/CMSSW_15_0_20/src && eval $(scram runtime -sh)
export SITECONFIG_PATH=/cvmfs/cms.cern.ch/SITECONF/T2_CH_CERN
scram b -j2 python >/dev/null 2>&1
cd /mnt/vdb/Codes/cmssw_dalitz_150
echo "### cmsRun both backends (15_0)"
cmsRun compare_backends_cfg.py > cmsrun_cmp.log 2>&1; echo "### RC=$?"
grep -iE 'Fatal|Exception|Error' cmsrun_cmp.log | head -5
echo "### compare xgboost vs onnx per electron"
python3 - <<'PY'
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
t=ROOT.TFile.Open("cmpBackends.root").Get("Events")
maxd=0.0; n=0; exact=0; rows=[]
for i in range(t.GetEntries()):
    t.GetEntry(i)
    for j in range(t.nElectron):
        x=t.Electron_mvaXgb[j]; o=t.Electron_mvaOnnx[j]; d=abs(x-o); n+=1
        if x==o: exact+=1
        if d>maxd: maxd=d
        if len(rows)<12: rows.append((t.Electron_pt[j], x, o, d, int(t.Electron_nGsf[j]), int(t.Electron_catXgb[j])))
print("electrons compared:", n)
print("exact bit matches: %d / %d" % (exact, n))
print("max |xgb - onnx|: %.3e" % maxd)
print("pt        xgboost         onnx           |diff|     nGsf cat")
for pt,x,o,d,ng,c in rows:
    print("  %6.1f  %.9f  %.9f  %.2e  %d   %d"%(pt,x,o,d,ng,c))
print("BACKENDS_MATCH" if maxd < 1e-5 else "BACKENDS_DIFFER")
PY
