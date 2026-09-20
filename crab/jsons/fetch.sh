#!/bin/bash
# Fetch the Run2 UL/Legacy golden JSONs used by crab_submit.py (GOLDEN_* lumimask tags).
set -e
cd "$(dirname "$0")"
BASE=https://cms-service-dqmdc.web.cern.ch/CAF/certification
curl -sfO $BASE/Collisions16/13TeV/Legacy_2016/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt
curl -sfO $BASE/Collisions17/13TeV/Legacy_2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt
curl -sfO $BASE/Collisions18/13TeV/Legacy_2018/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt
curl -sfO $BASE/Collisions22/Cert_Collisions2022_355100_362760_Golden.json
curl -sfO $BASE/Collisions23/Cert_Collisions2023_366442_370790_Golden.json
curl -sfO $BASE/Collisions24/Cert_Collisions2024_378981_386951_Golden.json
curl -sfO $BASE/Collisions25/Cert_Collisions2025_391658_398903_Golden.json
ls -la Cert_*
