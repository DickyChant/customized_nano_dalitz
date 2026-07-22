import FWCore.ParameterSet.Config as cms

# Common functions and classes for ID definition are imported here:
from RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_tools import EleWorkingPoint_V5
from ZprimeTo4l.ModifiedHEEP.Identification.modifiedCutBasedElectronID_tools import configureVIDModifiedCutBasedEleID_V5

# Loose working point (for fake factor study) Barrel and Endcap
idName = "modifiedCutBasedElectronID-Fall17-94X-V2-loose"
WP_Loose_EB = EleWorkingPoint_V5(
    idName                         = idName  , # idName
    full5x5_sigmaIEtaIEtaCut       = 0.0112  , # full5x5_sigmaIEtaIEtaCut
    dEtaInSeedCut                  = 0.00377 , # dEtaInSeedCut
    dPhiInCut                      = 0.0884  , # dPhiInCut
    hOverECut_C0                   = 0.05    , # hOverECut
    hOverECut_CE                   = 1.16    ,
    hOverECut_Cr                   = 0.0324  ,
    relCombIsolationWithEACut_C0   = 0.112   , # relCombIsolationWithEACut
    relCombIsolationWithEACut_Cpt  = 0.506   ,
    absEInverseMinusPInverseCut    = 0.193   , # absEInverseMinusPInverseCut
    # conversion veto cut needs no parameters, so not mentioned
    missingHitsCut                 = 1          # missingHitsCut
    )

WP_Loose_EE = EleWorkingPoint_V5(
    idName                         = idName  , # idName
    full5x5_sigmaIEtaIEtaCut       = 0.0425  , # full5x5_sigmaIEtaIEtaCut
    dEtaInSeedCut                  = 0.00674 , # dEtaInSeedCut
    dPhiInCut                      = 0.169   , # dPhiInCut
    hOverECut_C0                   = 0.0441  , # hOverECut
    hOverECut_CE                   = 2.54    ,
    hOverECut_Cr                   = 0.183   ,
    relCombIsolationWithEACut_C0   = 0.108   , # relCombIsolationWithEACut
    relCombIsolationWithEACut_Cpt  = 0.963   ,
    absEInverseMinusPInverseCut    = 0.111   , # absEInverseMinusPInverseCut
    # conversion veto cut needs no parameters, so not mentioned
    missingHitsCut                 = 1         # missingHitsCut
    )

# Tight working point (for non-isolated TnP study) Barrel and Endcap
idName = "modifiedCutBasedElectronID-Fall17-94X-V2-tight"
WP_Tight_EB = EleWorkingPoint_V5(
    idName                         = idName  , # idName
    full5x5_sigmaIEtaIEtaCut       = 0.0104  , # full5x5_sigmaIEtaIEtaCut
    dEtaInSeedCut                  = 0.00255 , # dEtaInSeedCut
    dPhiInCut                      = 0.022   , # dPhiInCut
    hOverECut_C0                   = 0.026   , # hOverECut
    hOverECut_CE                   = 1.15    ,
    hOverECut_Cr                   = 0.0324  ,
    relCombIsolationWithEACut_C0   = 13000.  , # ignored anyway (but to be sure)
    relCombIsolationWithEACut_Cpt  = 0.0     ,
    absEInverseMinusPInverseCut    = 0.159   , # absEInverseMinusPInverseCut
    # conversion veto cut needs no parameters, so not mentioned
    missingHitsCut                 = 1          # missingHitsCut
    )

WP_Tight_EE = EleWorkingPoint_V5(
    idName                         = idName  , # idName
    full5x5_sigmaIEtaIEtaCut       = 0.0353  , # full5x5_sigmaIEtaIEtaCut
    dEtaInSeedCut                  = 0.00501 , # dEtaInSeedCut
    dPhiInCut                      = 0.0236  , # dPhiInCut
    hOverECut_C0                   = 0.0188  , # hOverECut
    hOverECut_CE                   = 2.06    ,
    hOverECut_Cr                   = 0.183   ,
    relCombIsolationWithEACut_C0   = 13000.  , # ignored anyway (but to be sure)
    relCombIsolationWithEACut_Cpt  = 0.0     ,
    absEInverseMinusPInverseCut    = 0.0197  , # absEInverseMinusPInverseCut
    # conversion veto cut needs no parameters, so not mentioned
    missingHitsCut                 = 1          # missingHitsCut
    )

modifiedCutBasedElectronID_Fall17_94X_V2_loose = configureVIDModifiedCutBasedEleID_V5(WP_Loose_EB, WP_Loose_EE)
modifiedCutBasedElectronID_Fall17_94X_V2_tight = configureVIDModifiedCutBasedEleID_V5(WP_Tight_EB, WP_Tight_EE)
