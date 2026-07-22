#!/bin/bash
export SCRAM_ARCH=el9_amd64_gcc12
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz_150/CMSSW_15_0_20/src && eval $(scram runtime -sh)
export SITECONFIG_PATH=/cvmfs/cms.cern.ch/SITECONF/T2_CH_CERN
cd /mnt/vdb/Codes/cmssw_dalitz_150/gen_run3
N=20; GT=auto:phase1_2022_realistic; ERA=Run3

runstep() { local label=$1 out=$2; shift 2
  echo "### $label -> $out"
  cmsDriver.py "$@" -n $N --no_exec > ${label}_drv.log 2>&1
  [ -f ${label}.py ] || { echo "  cmsDriver FAILED"; tail -12 ${label}_drv.log; echo GEN_ABORT; exit 1; }
  cmsRun ${label}.py > ${label}.log 2>&1; local rc=$?
  echo "  rc=$rc size=$(ls -lh $out 2>/dev/null | awk '{print $5}') events=$(edmFileUtil -e -f file:$out 2>/dev/null | grep -oE '[0-9]+ events' | head -1)"
  if [ ! -s "$out" ]; then awk '/Begin Fatal Exception/{f=1} f{print} /End Fatal Exception/{f=0}' ${label}.log | head -16; echo GEN_ABORT; exit 1; fi
}

# RECO without the removed 'EI' step
runstep s3 s3.root s3 -s RAW2DIGI,L1Reco,RECO,RECOSIM --mc --era $ERA \
  --conditions $GT --eventcontent AODSIM --datatier AODSIM \
  --filein file:s2.root --python_filename s3.py --fileout file:s3.root

runstep s4 miniaod.root s4 -s PAT --mc --era $ERA --runUnscheduled \
  --conditions $GT --eventcontent MINIAODSIM --datatier MINIAODSIM \
  --filein file:s3.root --python_filename s4.py --fileout file:miniaod.root

echo "### GEN_RUN3_DONE miniaod=$(ls -lh miniaod.root 2>/dev/null | awk '{print $5}') events=$(edmFileUtil -e -f file:miniaod.root 2>/dev/null | grep -oE '[0-9]+ events' | head -1)"
