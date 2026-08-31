#!/bin/bash
# LPC (cmslpc, el9 native): set up CMSSW_15_0_20 and build the NanoDalitz packages
# (ZprimeTo4l ID producers + HDalitzEle MergedID + PhysicsTools/NanoDalitz) from this repo.
set -e
export SCRAM_ARCH=el9_amd64_gcc12
source /cvmfs/cms.cern.ch/cmsset_default.sh

BASE=${CND_BASE:-/uscms_data/d3/sitianq/nu_dalitz}
REPO=$BASE/customized_nano_dalitz

cd "$BASE"
if [ ! -d CMSSW_15_0_20 ]; then
  echo "### scram project CMSSW_15_0_20"
  scram project CMSSW CMSSW_15_0_20
fi
cd CMSSW_15_0_20/src
eval $(scram runtime -sh)   # cmsenv

echo "### sync packages from $REPO"
rsync -a --delete "$REPO/ZprimeTo4l/"   ZprimeTo4l/
rsync -a --delete "$REPO/PhysicsTools/" PhysicsTools/
rsync -a --delete "$REPO/HDalitzEle/"   HDalitzEle/

echo "### scram b -j8"
scram b -j8 2>&1 | tail -30
echo "### BUILD_DONE"
