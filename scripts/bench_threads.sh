#!/bin/bash
# Benchmark the customized-nano job at 1/2/4 threads: peak RSS + throughput.
# Answers "how should CRAB numCores / maxMemoryMB be set for the _15X production?".
set -e
export SCRAM_ARCH=el9_amd64_gcc12
source /cvmfs/cms.cern.ch/cmsset_default.sh
export X509_USER_PROXY=${X509_USER_PROXY:-/uscms/home/sitianq/x509up_u25265}
cd /uscms_data/d3/sitianq/nu_dalitz/CMSSW_15_0_20/src && eval $(scram runtime -sh)

# default to the LPC 3-day scratch: this pulls a ~1 GB MINIAOD and writes test nano,
# none of which belongs in the (quota'd, backed-up) project area
WORK=${1:-/uscmst1b_scratch/lpc1/3DayLifetime/$USER/nu_dalitz_bench}
NEV=${NEV:-300}
LFN=/store/mc/RunIISummer20UL18MiniAODv2/GluGluHToEEG_M125_Dalitz_012j_TuneCP5_13TeV_amcatnlo_pythia8/MINIAODSIM/106X_upgrade2018_realistic_v16_L1v1-v3/40000/EF1384F9-F399-FE43-8FCD-1732F0EFF2FC.root
mkdir -p "$WORK" && cd "$WORK"

# local copy so xrootd latency doesn't pollute the timing
if [ ! -f input.root ]; then
  echo "### fetching test MINIAOD"
  xrdcp -f "root://cmsxrootd.fnal.gov/$LFN" input.root
fi
ls -lh input.root

for NT in 1 2 4; do
  PSET=pset_nt${NT}.py
  if [ ! -f "$PSET" ]; then
    cmsDriver.py bench_nt${NT} -s NANO --mc \
      --era Run2_2018,run2_nanoAOD_106Xv2 --conditions 106X_upgrade2018_realistic_v16_L1v1 \
      --customise PhysicsTools/NanoDalitz/nano_cff.customizeAllMergedElectron2018,PhysicsTools/NanoDalitz/nano_cff.slimNanoDalitz \
      --eventcontent NANOAODSIM --datatier NANOAODSIM \
      --filein file:input.root --fileout file:out_nt${NT}.root \
      --nThreads $NT -n $NEV --no_exec --python_filename "$PSET" > /dev/null 2>&1
  fi
  echo "### === nThreads=$NT ($NEV events) ==="
  /usr/bin/time -v cmsRun "$PSET" > log_nt${NT}.txt 2> time_nt${NT}.txt || {
      echo "  RUN FAILED (rc=$?)"; tail -20 time_nt${NT}.txt; continue; }
  WALL=$(grep "Elapsed (wall clock)" time_nt${NT}.txt | awk '{print $NF}')
  RSS=$(grep "Maximum resident set size" time_nt${NT}.txt | awk '{print $NF}')
  CPU=$(grep "Percent of CPU this job got" time_nt${NT}.txt | awk '{print $NF}')
  echo "  wall=$WALL  peakRSS=$((RSS/1024)) MB  cpu=$CPU  out=$(ls -la out_nt${NT}.root 2>/dev/null | awk '{print $5}')"
done
echo "### BENCH_DONE"
