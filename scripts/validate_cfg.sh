#!/bin/bash
set -e
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src
eval $(scram runtime -sh)

echo "### scram b (pick up NanoDalitz python)"
scram b -j4 python 2>&1 | tail -5 || scram b -j4 2>&1 | tail -5

cd /mnt/vdb/Codes/cmssw_dalitz
echo "### cmsDriver: generate nano cfg (no exec)"
cmsDriver.py nanoDalitz -s NANO --mc --eventcontent NANOAODSIM --datatier NANOAODSIM \
  --era Run2_2018 --conditions 106X_upgrade2018_realistic_v16 \
  --customise PhysicsTools/NanoDalitz/nano_cff.customizeMergedElectron2018 \
  --filein file:dummy_MiniAOD.root --fileout file:nanoDalitz.root -n 10 \
  --no_exec --python_filename nanoDalitz_cfg.py 2>&1 | tail -15

echo "### inspect generated cfg for our external variables"
python3 - <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("cfg", "nanoDalitz_cfg.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
p = m.process
ev = p.electronTable.externalVariables
names = [k for k in ev.parameters_()]
print("electronTable.externalVariables:", names)
assert "mvaMergedElectron" in names, "missing mvaMergedElectron"
assert "mvaMergedElectronCategory" in names, "missing category"
print("mergedHEEPIDVarValueMaps present:", hasattr(p, "mergedHEEPIDVarValueMaps"))
print("mergedLeptonIDProducer present:", hasattr(p, "mergedLeptonIDProducer"))
print("mergedLeptonIDProducer.srcEle:", p.mergedLeptonIDProducer.srcEle.value())
print("heep.elesMiniAOD:", p.mergedHEEPIDVarValueMaps.elesMiniAOD.value())
print("CONFIG_OK")
PY
