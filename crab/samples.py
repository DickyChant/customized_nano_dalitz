"""Sample list for the customized-NanoAOD (merged-electron ID) CRAB production.

Each entry: name, dataset (DAS), era, globaltag, isData, customise, [lumimask].
Datasets and (nfiles, nevents) validated via DAS on 2026-07-22.

Branch note:
  * CMSSW_10_6_X handles the Run2 UL entries (both merged IDs).
  * CMSSW_15_0_X handles Run2 UL AND Run3 (Run3 runs the HDalitz ID only; the ZprimeTo4l
    GBRForest models are Run2-UL-trained).
Run only the entries appropriate to the release you checked out (submit.py filters by --release).
"""

# UL golden JSON for data (adjust the path on lxplus if needed)
GOLDEN_2018 = ("/cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/../.."  # placeholder root
               )  # see README: use the official Cert_..._Legacy2018_Collisions18_JSON.txt

SAMPLES = [
    # ---- Run2 UL MC (both branches) : DY M-50 amcatnloFXFX ----
    dict(name="DYJetsToLL_M50_UL16APV", release="10_6",
         dataset="/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16MiniAODAPVv2-106X_mcRun2_asymptotic_preVFP_v11-v1/MINIAODSIM",
         era="Run2_2016_HIPM,run2_nanoAOD_106Xv2", globaltag="106X_mcRun2_asymptotic_preVFP_v11",
         isData=False, customise="PhysicsTools/NanoDalitz/nano_cff.customizeAllMergedElectron2016APV"),   # 980 files, 91M evt
    dict(name="DYJetsToLL_M50_UL16", release="10_6",
         dataset="/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16MiniAODv2-106X_mcRun2_asymptotic_v17-v1/MINIAODSIM",
         era="Run2_2016,run2_nanoAOD_106Xv2", globaltag="106X_mcRun2_asymptotic_v17",
         isData=False, customise="PhysicsTools/NanoDalitz/nano_cff.customizeAllMergedElectron2016"),      # 822 files, 74M evt
    dict(name="DYJetsToLL_M50_UL17", release="10_6",
         dataset="/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/MINIAODSIM",
         era="Run2_2017,run2_nanoAOD_106Xv2", globaltag="106X_mc2017_realistic_v9",
         isData=False, customise="PhysicsTools/NanoDalitz/nano_cff.customizeAllMergedElectron2017"),      # 3563 files, 196M evt
    dict(name="DYJetsToLL_M50_UL18", release="10_6",
         dataset="/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
         era="Run2_2018,run2_nanoAOD_106Xv2", globaltag="106X_upgrade2018_realistic_v16_L1v1",
         isData=False, customise="PhysicsTools/NanoDalitz/nano_cff.customizeAllMergedElectron2018"),      # 2465 files, 196M evt

    # ---- Run2 UL DATA (both branches) : EGamma 2018D UL ----
    dict(name="EGamma_Run2018D_UL", release="10_6",
         dataset="/EGamma/Run2018D-UL2018_MiniAODv2-v2/MINIAOD",
         era="Run2_2018,run2_nanoAOD_106Xv2", globaltag="106X_dataRun2_v35",
         isData=True, lumimask="GOLDEN_2018",
         customise="PhysicsTools/NanoDalitz/nano_cff.customizeAllMergedElectron2018"),                    # 10123 files, 752M evt

    # ---- Run3 2022 MC (CMSSW_15_0_X only) : DYto2E powheg (HDalitz ID only) ----
    dict(name="DYto2E_M50_Run3Summer22", release="15_0",
         dataset="/DYto2E_M-50_NNPDF31_TuneCP5_13p6TeV-powheg-pythia8/Run3Summer22MiniAODv4-130X_mcRun3_2022_realistic_v5-v2/MINIAODSIM",
         era="Run3", globaltag="130X_mcRun3_2022_realistic_v5",
         isData=False, customise="PhysicsTools/NanoDalitz/nano_cff.customizeHDalitzMergedElectron"),
]
