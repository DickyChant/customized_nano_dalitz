#!/bin/bash
# Native el9 CMSSW_15_0_20. Copy the ID producers from the 10_6 tree and attempt a build.
export SCRAM_ARCH=el9_amd64_gcc12
source /cvmfs/cms.cern.ch/cmsset_default.sh
BASE=/mnt/vdb/Codes/cmssw_dalitz_150
SRC10=/mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src
cd "$BASE"
if [ ! -d CMSSW_15_0_20 ]; then
  echo "### scram project CMSSW_15_0_20"
  scram project CMSSW CMSSW_15_0_20
fi
cd CMSSW_15_0_20/src
eval $(scram runtime -sh)

if [ ! -d ZprimeTo4l ]; then
  echo "### copy ZprimeTo4l (ModifiedHEEP + MergedLepton, with dictionaries) + PhysicsTools/NanoDalitz"
  mkdir -p ZprimeTo4l PhysicsTools
  cp -r "$SRC10/ZprimeTo4l/ModifiedHEEP" ZprimeTo4l/
  cp -r "$SRC10/ZprimeTo4l/MergedLepton" ZprimeTo4l/
  cp -r "$SRC10/PhysicsTools/NanoDalitz" PhysicsTools/
fi

echo "### scram b (expect API errors to fix)"
scram b -j8 2>&1 | grep -iE 'error:|Error |cannot|no member|no matching|undeclared|not declared|no type named|BUILD_DONE|Entering|Leaving Package' | head -80
echo "### FIRST_BUILD_DONE"
