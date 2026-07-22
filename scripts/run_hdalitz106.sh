#!/bin/bash
export SCRAM_ARCH=slc7_amd64_gcc700; source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /mnt/vdb/Codes/cmssw_dalitz/CMSSW_10_6_39/src && eval $(scram runtime -sh)
export CMS_PATH=/mnt/vdb/Codes/cmssw_dalitz/siteoverlay
cd /mnt/vdb/Codes/cmssw_dalitz
echo "### cmsRun HDalitz ONNX in 10_6"
( while true; do ps -o rss= -C cmsRun 2>/dev/null|awk '{s+=$1}END{if(s)print "  RSS MB:",int(s/1024)}'; sleep 8; done ) & MON=$!
cmsRun hdalitz106_cfg.py > cmsrun_hdal106.log 2>&1; RC=$?; kill $MON 2>/dev/null
echo "### RC=$RC"
grep -iE 'Fatal|Exception|Error|onnx|Ort' cmsrun_hdal106.log | head -6
