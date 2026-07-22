#!/bin/bash
# Runs INSIDE the cmssw-el7 container. Sets up CMSSW_10_6_39, checks out the
# ZprimeTo4l ID producers (ModifiedHEEP + MergedLepton only), builds them.
set -e
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz

if [ ! -d CMSSW_10_6_39 ]; then
  echo "### cmsrel CMSSW_10_6_39"
  scram project CMSSW CMSSW_10_6_39
fi
cd CMSSW_10_6_39/src
eval $(scram runtime -sh)   # cmsenv

if [ ! -d ZprimeTo4l ]; then
  echo "### clone ZprimeTo4l"
  git clone -q https://github.com/SanghyunKo/ZprimeTo4l.git ZprimeTo4l
  # out-of-scope: analysis package (needs external TnP/Egamma deps)
  rm -rf ZprimeTo4l/Analysis
  # keep only the ID producer + its direct helpers in MergedLepton/plugins;
  # drop the training/validation analyzers (not needed, extra deps)
  cd ZprimeTo4l/MergedLepton/plugins
  for f in MergedEleBkgMvaInput.cc MergedEleSigAnalyzer.cc MergedEleSigMvaInput.cc \
           MergedLeptonIDConversionAnalyzer.cc MergedLeptonIDJpsiAnalyzer.cc; do
    [ -f "$f" ] && rm -f "$f" && echo "  dropped $f"
  done
  cd /mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src
fi

echo "### scram build (ModifiedHEEP + MergedLepton)"
scram b -j 8 2>&1 | tail -40
echo "### BUILD_DONE rc=$?"
