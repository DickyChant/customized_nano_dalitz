"""Trigger efficiency as two independent histograms, and their ratio.

  gen-binned : full denominator (reco photon + reco electron matched to gen), binned in the
               generated pair variable -- the perfect-resolution performance.
  reco-binned: the subset that HAS a reco pair observable (resolved -> two reco electrons;
               merged -> 2 GSF tracks), binned in the reconstructed variable.

The two samples are NOT the same events: the reco histogram cannot contain merged 1-GSF
candidates, which have no reconstructible pair mass. The ratio therefore mixes migration
with that population difference -- which is the point of the comparison.
"""
import os, ROOT, glob, sys, json
ROOT.gROOT.SetBatch(True); ROOT.EnableImplicitMT(8)
mass = sys.argv[1] if len(sys.argv) > 1 else "M125"
files = sorted(glob.glob(f"/eos/uscms/store/user/cromerom/nanoDalitz_v3/*H*EEG_{mass}_*/*_{mass}_UL18_15X/*/*/*.root"))
print(len(files), "files")
ROOT.gInterpreter.Declare(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_helpers.h")).read())
df = ROOT.RDataFrame("Events", files)
df = (df.Define("w", "genWeight>0 ? 1.f : -1.f")
        .Define("gE", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 11)")
        .Define("gG", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 22)")
        .Filter("gE.size()==2 && gG.size()==1", "2 gen e + 1 gen pho")
        .Define("e1", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[0]],GenPart_eta[gE[0]],GenPart_phi[gE[0]],0.000511)")
        .Define("e2", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[1]],GenPart_eta[gE[1]],GenPart_phi[gE[1]],0.000511)")
        .Define("mgs_gen", "(float)(e1+e2).M()")
        .Define("dRee_gen", "(float)ROOT::VecOps::DeltaR(e1.Eta(),e2.Eta(),e1.Phi(),e2.Phi())")
        .Define("gEta", "GenPart_eta[gG[0]]").Define("gPhi", "GenPart_phi[gG[0]]")
        .Define("rPho", "nMatch(gEta,gPhi,Photon_eta,Photon_phi,Photon_pt,35.f)")
        .Define("rE1", "nMatch(e1.Eta(),e1.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rE2", "nMatch(e2.Eta(),e2.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rEleLeadPt", "float p=0; if(rE1>=0) p=std::max(p,Electron_pt[rE1]); if(rE2>=0) p=std::max(p,Electron_pt[rE2]); return p;")
        .Filter("rPho>=0 && rEleLeadPt>25", "reco photon + electron matched")
        .Define("category", "(rE1>=0&&rE2>=0) ? (rE1==rE2 ? 2 : 1) : 0")
        .Define("has2Gsf", "category==2 && Electron_gsfHasAddTrk[rE1]==1")
        .Define("mgs_reco", "if (category==1) { ROOT::Math::PtEtaPhiMVector a(Electron_pt[rE1],Electron_eta[rE1],Electron_phi[rE1],0.000511),"
                            "                                             b(Electron_pt[rE2],Electron_eta[rE2],Electron_phi[rE2],0.000511);"
                            "  return (float)(a+b).M(); }"
                            "else if (has2Gsf) return Electron_gsfDiTrkMass[rE1]; else return -999.f;")
        .Define("dRee_reco", "if (category==1) return (float)ROOT::VecOps::DeltaR(Electron_eta[rE1],Electron_eta[rE2],Electron_phi[rE1],Electron_phi[rE2]);"
                             "else if (has2Gsf) return Electron_gsfDeltaR[rE1]; else return -999.f;")
        .Define("hasReco", "mgs_reco > -1")
        .Define("passOR", "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90"
                          " || HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55"))
TRIGS = {"Dipho30_22": "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90",
         "Dipho30_18": "HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55",
         "OR": "passOR"}
from array import array
EDGES = {"mgs": array('d',[0,1,2,3,4,5,6,7,8,9,10,15,20,30,40,50,60]),
         "dRee": array('d',[0,0.03,0.06,0.09,0.12,0.16,0.22,0.3,0.4,0.55,0.7,0.85,1])}
H = {}
dfs = {"gen": df, "reco": df.Filter("hasReco", "reco pair observable defined")}
for v, e in EDGES.items():
    for lvl in ("gen", "reco"):
        col = f"{v}_{lvl}"; dd = dfs[lvl]
        H[(v,lvl,"den")] = dd.Histo1D((f"{v}{lvl}den","",len(e)-1,e), col, "w")
        for tn, tc in TRIGS.items():
            H[(v,lvl,tn)] = dd.Filter(tc).Histo1D((f"{v}{lvl}{tn}","",len(e)-1,e), col, "w")
        # reconstruction-category counts, no trigger requirement: resolved vs merged.
        # In the reco binning "merged" can only be the 2-GSF kind (1-GSF has no pair observable).
        merged = "category==2" if lvl == "gen" else "has2Gsf"
        H[(v,lvl,"nRes")] = dd.Filter("category==1").Histo1D((f"{v}{lvl}nRes","",len(e)-1,e), col, "w")
        H[(v,lvl,"nMer")] = dd.Filter(merged).Histo1D((f"{v}{lvl}nMer","",len(e)-1,e), col, "w")
rep = df.Report()
out = {}
for v, e in EDGES.items():
    out[v] = {}
    for lvl in ("gen", "reco"):
        den = H[(v,lvl,"den")]; rows = []
        for i in range(1, den.GetNbinsX()+1):
            N = den.GetBinContent(i); row = {"lo": e[i-1], "hi": e[i], "den": N,
                                             "nRes": H[(v,lvl,"nRes")].GetBinContent(i),
                                             "nMer": H[(v,lvl,"nMer")].GetBinContent(i)}
            for tn in TRIGS:
                n = H[(v,lvl,tn)].GetBinContent(i)
                eff = n/N if N > 0 else 0
                err = ((max(eff*(1-eff), 0.0)/N)**0.5) if N > 0 else 0.0
                row[tn] = [eff, err]
            rows.append(row)
        out[v][lvl] = rows
rep.Print()
json.dump(out, open(f"trigeff_ratio_{mass}.json","w"), indent=1)
print("wrote trigeff_ratio_%s.json" % mass)
