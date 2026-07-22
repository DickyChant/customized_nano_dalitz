#!/bin/bash
export SCRAM_ARCH=el9_amd64_gcc12; source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz_150/CMSSW_15_0_20/src && eval $(scram runtime -sh)
scram b -j4 2>&1 | grep -iE 'error:|fatal|cannot|no member|no matching|not declared|no type|undefined|Leaving Package|BUILD' | head -50
echo HDALITZ_BUILD_DONE
