#!/bin/bash
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
export CMS_PATH=/mnt/vdb/Codes/cmssw_dalitz/siteoverlay
cd /mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src && eval $(scram runtime -sh)
cd /mnt/vdb/Codes/cmssw_dalitz/gen
N=20; GT=106X_upgrade2018_realistic_v16_L1v1; ERA=Run2_2018

runstep() { local label=$1 out=$2; shift 2
  echo "### $label -> $out"
  cmsDriver.py "$@" -n $N --no_exec > ${label}_drv.log 2>&1
  [ -f ${label}.py ] || { echo "  cmsDriver FAILED"; tail -12 ${label}_drv.log; echo GEN_ABORT; exit 1; }
  cmsRun ${label}.py > ${label}.log 2>&1; local rc=$?
  echo "  rc=$rc size=$(ls -lh $out 2>/dev/null | awk '{print $5}') events=$(edmFileUtil -e -f file:$out 2>/dev/null | grep -oE '[0-9]+ events' | head -1)"
  if [ ! -s "$out" ]; then awk '/Begin Fatal Exception/{f=1} f{print} /End Fatal Exception/{f=0}' ${label}.log | head -16; echo GEN_ABORT; exit 1; fi
}

# step2: DIGI + RAW + fake HLT (separate from RECO to avoid the TriggerResults cycle)
runstep s2 s2.root s2 -s DIGI,L1,DIGI2RAW,HLT:Fake2 --mc --era $ERA \
  --conditions $GT --eventcontent FEVTDEBUGHLT --datatier GEN-SIM-DIGI-RAW \
  --filein file:s1.root --python_filename s2.py --fileout file:s2.root

# step3: RECO -> AODSIM
runstep s3 s3.root s3 -s RAW2DIGI,L1Reco,RECO,RECOSIM,EI --mc --era $ERA \
  --conditions $GT --eventcontent AODSIM --datatier AODSIM \
  --filein file:s2.root --python_filename s3.py --fileout file:s3.root

# step4: PAT -> MINIAOD
runstep s4 miniaod.root s4 -s PAT --mc --era $ERA --runUnscheduled \
  --conditions $GT --eventcontent MINIAODSIM --datatier MINIAODSIM \
  --filein file:s3.root --python_filename s4.py --fileout file:miniaod.root

echo "### GEN_DONE miniaod=$(ls -lh miniaod.root 2>/dev/null | awk '{print $5}') events=$(edmFileUtil -e -f file:miniaod.root 2>/dev/null | grep -oE '[0-9]+ events' | head -1)"
