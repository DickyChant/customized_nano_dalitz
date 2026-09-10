#!/usr/bin/env python3
"""Validate a customized-NanoAOD file: structure, required branches, and physics sanity.

Works on a local path or any xrootd/davs URL ROOT can open, e.g.

    python3 validate_nano.py nano.root
    python3 validate_nano.py root://cmseos.fnal.gov//store/user/sqian/nanoDalitz_v2/.../nano_1.root
    python3 validate_nano.py --quiet f1.root f2.root      # batch; exit code is what matters

Exit code 0 = all checks passed, 1 = at least one FAIL. WARN does not fail the run
(a file can legitimately contain no merged-electron candidates if it is small).

Run inside a CMSSW area (`cmsenv`) so PyROOT is available.
"""
import argparse
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kError

# Branches the H->ee gamma analysis needs. Grouped so a failure says *what* is missing.
REQUIRED = {
    "merged ID": [
        "Electron_mvaMergedElectron", "Electron_mvaMergedElectronCategory",
        "Electron_mvaHDalitzMergedID", "Electron_hdalitzMergedCategory",
        "Electron_hdalitzMergedNGsf", "Electron_hdalitzMergedWPTight",
    ],
    "GSF tracks": [
        "Electron_gsfHasAddTrk",
        "Electron_gsfMainTrkPt", "Electron_gsfMainTrkEta", "Electron_gsfMainTrkPhi",
        "Electron_gsfMainTrkD0", "Electron_gsfMainTrkDz", "Electron_gsfMainTrkCharge",
        "Electron_gsfMainTrkMissHits", "Electron_gsfMainTrkLostHits",
        "Electron_gsfMainTrkPixelHits", "Electron_gsfMainTrkLayers",
        "Electron_gsfAddTrkPt", "Electron_gsfAddTrkEta", "Electron_gsfAddTrkPhi",
        "Electron_gsfAddTrkD0", "Electron_gsfAddTrkDz", "Electron_gsfAddTrkCharge",
        "Electron_gsfAddTrkMissHits", "Electron_gsfAddTrkLostHits",
        "Electron_gsfAddTrkPixelHits", "Electron_gsfAddTrkLayers",
        "Electron_gsfPtRatio", "Electron_gsfDeltaR", "Electron_gsfRelPtRatio",
        "Electron_gsfPtSum", "Electron_gsfDiTrkPt", "Electron_gsfDiTrkMass",
    ],
    "ID inputs": [
        "Electron_dEtaSCTrkAtVtx", "Electron_dPhiSCTrkAtVtx", "Electron_scEtaWidth",
        "Electron_scPhiWidth", "Electron_sipip", "Electron_eSCOverP",
        "Electron_eEleOverPout", "Electron_gsfTrkChi2",
    ],
    # supercluster phi is the 4th energy-regression feature AND is what the Hgg
    # preselection matches electron<->photon on, so it is required on both collections
    "supercluster": [
        "Electron_superclusterEta", "Electron_superclusterPhi", "Electron_superclusterEnergy",
        "Electron_rawEnergy", "Electron_PreshowerEnergy",
        "Electron_esEnergyPlane1", "Electron_esEnergyPlane2",
        "Photon_superclusterEta", "Photon_superclusterPhi", "Photon_superclusterEnergy",
        "Photon_esEnergyPlane1", "Photon_esEnergyPlane2",
    ],
    "isolation": [
        "Electron_pfChIso", "Electron_pfPhoIso", "Electron_pfNeuIso", "Electron_pfPUIso",
        "Electron_ecalPFClusIso", "Electron_hcalPFClusIso",
    ],
    "EGM syst": [
        "Electron_egmScaleStatUp", "Electron_egmScaleStatDn", "Electron_egmScaleSystUp",
        "Electron_egmScaleGainUp", "Electron_egmResolRhoUp", "Electron_egmResolPhiUp",
        "Electron_egmEnergyPostCorr", "Electron_egmEnergyTrkPostCorr",
        "Photon_egmScaleStatUp", "Photon_egmResolRhoUp", "Photon_egmEnergyPostCorr",
    ],
    "analysis basics": [
        "Electron_pt", "Electron_eta", "Photon_pt", "Photon_mvaID", "Photon_s4",
        "Photon_etaWidth", "Photon_phiWidth", "Photon_esEffSigmaRR",
        "Rho_fixedGridRhoAll", "Rho_fixedGridRhoFastjetAll", "PV_npvsGood",
    ],
    "slim (must be ABSENT)": [],   # handled separately
}
# The merged-electron ENERGY REGRESSION input set (HDalitzEle MergedAnalysis.cpp:524-548).
# The regression itself runs downstream, so the file is only useful if every input is here.
REGRESSION_INPUTS = [
    "Rho_fixedGridRhoFastjetAll", "PV_npvs",
    "Electron_superclusterEta", "Electron_superclusterPhi", "Electron_rawEnergy", "Electron_pt",
    "Electron_dEtaSCTrkAtVtx", "Electron_dPhiSCTrkAtVtx", "Electron_energyErr", "Electron_hoe",
    "Electron_eSCOverP", "Electron_eEleOverPout", "Electron_eInvMinusPInv",
    "Electron_scEtaWidth", "Electron_scPhiWidth", "Electron_sieie", "Electron_sipip",
    "Electron_r9", "Electron_fbrem",
    "Electron_gsfPtSum", "Electron_gsfPtRatio", "Electron_gsfDiTrkPt", "Electron_gsfDeltaR",
    "Electron_PreshowerEnergy",   # EE-only eleESEnToRawE = PreshowerEnergy / rawEnergy
]

# --slim drops these; their presence means the customise did not run as intended
MUST_BE_ABSENT = ["boostedTau_pt", "LowPtElectron_pt", "FatJet_pt", "SubJet_pt", "IsoTrack_pt"]


class Report:
    def __init__(self):
        self.fail, self.warn, self.ok = [], [], []

    def check(self, cond, msg, warn_only=False):
        (self.ok if cond else (self.warn if warn_only else self.fail)).append(msg)
        return cond


def validate(path, quiet=False):
    r = Report()
    say = (lambda *a: None) if quiet else print
    say("=" * 78)
    say("FILE  %s" % path)

    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        print("  FAIL  cannot open file (zombie or missing)")
        return False
    if f.TestBit(ROOT.TFile.kRecovered):
        r.check(False, "file was RECOVERED -> it was not closed cleanly; job likely died")

    t = f.Get("Events")
    if not t:
        print("  FAIL  no 'Events' tree")
        return False
    n = t.GetEntries()
    r.check(n > 0, "Events tree has %d entries" % n)
    runs = f.Get("Runs")
    say("  events=%d  runs-tree=%s  size=%.1f MB"
        % (n, "yes" if runs else "NO", f.GetSize() / 1024.0 ** 2))

    names = {b.GetName() for b in t.GetListOfBranches()}
    say("  total branches: %d" % len(names))

    # --- required branches -------------------------------------------------
    for group, blist in REQUIRED.items():
        if not blist:
            continue
        missing = [b for b in blist if b not in names]
        r.check(not missing, "%-18s %d/%d present%s"
                % (group, len(blist) - len(missing), len(blist),
                   ("  MISSING: " + ", ".join(missing[:6])) if missing else ""))
    miss_reg = [b for b in REGRESSION_INPUTS if b not in names]
    r.check(not miss_reg, "energy-regression inputs %d/%d present%s"
            % (len(REGRESSION_INPUTS) - len(miss_reg), len(REGRESSION_INPUTS),
               ("  MISSING: " + ", ".join(miss_reg)) if miss_reg else ""))

    present_bad = [b for b in MUST_BE_ABSENT if b in names]
    r.check(not present_bad, "slim applied (dropped tables absent)%s"
            % ("  UNEXPECTEDLY PRESENT: " + ", ".join(present_bad) if present_bad else ""))

    # --- physics sanity on the merged-electron block -----------------------
    # Guard every branch this block touches: a missing one must FAIL cleanly, not traceback.
    need = ["nElectron", "Electron_gsfHasAddTrk", "Electron_gsfMainTrkCharge",
            "Electron_gsfAddTrkCharge", "Electron_gsfAddTrkMissHits", "Electron_gsfDiTrkMass",
            "Electron_gsfDeltaR", "Electron_gsfPtSum", "Electron_gsfMainTrkPt",
            "Electron_gsfAddTrkPt"]
    absent = [b for b in need if b not in names]
    if absent:
        r.check(False, "cannot run physics checks, branches absent: %s" % ", ".join(absent))
        f.Close()
        for m in r.ok:
            say("  ok    %s" % m)
        for m in r.warn:
            say("  WARN  %s" % m)
        for m in r.fail:
            say("  FAIL  %s" % m)
        say("  => FAIL")
        return False

    nele = nadd = opp = badmiss = 0
    masses, drs, ptsum_bad = [], [], 0
    for i in range(n):
        t.GetEntry(i)
        for j in range(int(t.nElectron)):
            nele += 1
            if int(t.Electron_gsfHasAddTrk[j]) != 1:
                continue
            nadd += 1
            if t.Electron_gsfMainTrkCharge[j] * t.Electron_gsfAddTrkCharge[j] < 0:
                opp += 1
            if int(t.Electron_gsfAddTrkMissHits[j]) != 0:
                badmiss += 1
            masses.append(t.Electron_gsfDiTrkMass[j])
            drs.append(t.Electron_gsfDeltaR[j])
            s, a, b = (t.Electron_gsfPtSum[j], t.Electron_gsfMainTrkPt[j], t.Electron_gsfAddTrkPt[j])
            if s > 0 and abs(s - (a + b)) / s > 1e-3:   # 1e-3 >> the ~6e-5 float-storage error
                ptsum_bad += 1

    say("  electrons=%d  with 2nd GSF track=%d (%.1f%%)"
        % (nele, nadd, 100.0 * nadd / nele if nele else 0.0))
    if nadd == 0:
        r.check(False, "no merged-electron candidates in this file -- cannot check physics",
                warn_only=True)
    else:
        # the association *requires* opposite sign and zero missing inner hits on the 2nd track
        r.check(opp == nadd, "opposite-sign main/add charge: %d/%d" % (opp, nadd))
        r.check(badmiss == 0, "2nd track missing-inner-hits==0: %d violations" % badmiss)
        r.check(ptsum_bad == 0, "gsfPtSum == mainPt+addPt: %d violations" % ptsum_bad)
        mmin, mmax = min(masses), max(masses)
        med = sorted(masses)[len(masses) // 2]
        r.check(mmin >= 0.0, "di-track mass non-negative (min=%.4f)" % mmin)
        r.check(med < 5.0, "di-track mass median %.4f GeV (merged pairs should be low-mass)" % med,
                warn_only=True)
        say("  di-track mass: min=%.4f med=%.4f max=%.4f GeV | dR med=%.5f"
            % (mmin, med, mmax, sorted(drs)[len(drs) // 2]))

    # --- EGM reference consistency (electrons vary the ECAL+track energy) --
    if "Electron_egmScaleStatUp" in names and nele:
        near_trk = near_ecal = 0
        for i in range(min(n, 200)):
            t.GetEntry(i)
            for j in range(int(t.nElectron)):
                up, ne, nt = (t.Electron_egmScaleStatUp[j], t.Electron_egmEnergyPostCorr[j],
                              t.Electron_egmEnergyTrkPostCorr[j])
                if up <= -900 or ne <= 0 or nt <= 0:
                    continue
                near_trk += abs(up - nt) <= abs(up - ne)
                near_ecal += abs(up - nt) > abs(up - ne)
        if near_trk + near_ecal:
            r.check(near_trk >= near_ecal,
                    "EGM electron variations track ecalTrkEnergyPostCorr (%d vs %d)"
                    % (near_trk, near_ecal))

    f.Close()
    for m in r.ok:
        say("  ok    %s" % m)
    for m in r.warn:
        say("  WARN  %s" % m)
    for m in r.fail:
        say("  FAIL  %s" % m)
    say("  => %s" % ("PASS" if not r.fail else "FAIL"))
    return not r.fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="local paths or xrootd/davs URLs")
    ap.add_argument("--quiet", action="store_true", help="only print the final verdict")
    a = ap.parse_args()
    results = [(p, validate(p, a.quiet)) for p in a.files]
    npass = sum(1 for _, v in results if v)
    print("\n%d/%d file(s) passed" % (npass, len(results)))
    for p, v in results:
        if not v:
            print("  FAILED: %s" % p)
    sys.exit(0 if npass == len(results) else 1)


if __name__ == "__main__":
    main()
