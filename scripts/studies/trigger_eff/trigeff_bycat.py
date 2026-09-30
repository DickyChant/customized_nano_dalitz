"""Trigger efficiency split by RECONSTRUCTION CATEGORY, plus the per-bin composition.

Binned in the generated variable, which is defined for every category (the reco pair
observable is not: merged 1-GSF candidates have none).
Categories: resolved (two reco electrons) | merged 2 GSF | merged 1 GSF | unmatched.
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
        .Define("mgs", "(float)(e1+e2).M()")
        .Define("dRee", "(float)ROOT::VecOps::DeltaR(e1.Eta(),e2.Eta(),e1.Phi(),e2.Phi())")
        .Define("gEta", "GenPart_eta[gG[0]]").Define("gPhi", "GenPart_phi[gG[0]]")
        .Define("rPho", "nMatch(gEta,gPhi,Photon_eta,Photon_phi,Photon_pt,35.f)")
        .Define("rE1", "nMatch(e1.Eta(),e1.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rE2", "nMatch(e2.Eta(),e2.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rEleLeadPt", "float p=0; if(rE1>=0) p=std::max(p,Electron_pt[rE1]); if(rE2>=0) p=std::max(p,Electron_pt[rE2]); return p;")
        .Filter("rPho>=0 && rEleLeadPt>25", "reco photon + electron matched")
        # 1 = resolved, 2 = merged with 2 GSF tracks, 3 = merged with only 1 GSF track
        .Define("cat", "if (rE1>=0 && rE2>=0 && rE1!=rE2) return 1;"
                       "else if (rE1>=0 && rE1==rE2) return Electron_gsfHasAddTrk[rE1]==1 ? 2 : 3;"
                       "else return 0;")
        .Define("passOR", "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90"
                          " || HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55"))
TRIGS = {"Dipho30_22": "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90",
         "Dipho30_18": "HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55",
         "OR": "passOR"}
CATS = {1: "resolved", 2: "merged2Gsf", 3: "merged1Gsf", 0: "unmatched"}
from array import array
EDGES = {"mgs": array('d',[0,1,2,3,4,5,6,7,8,9,10,15,20,30,40,50,60]),
         "dRee": array('d',[0,0.03,0.06,0.09,0.12,0.16,0.22,0.3,0.4,0.55,0.7,0.85,1])}
H = {}
for v, e in EDGES.items():
    H[(v,"all","den")] = df.Histo1D((f"{v}allden","",len(e)-1,e), v, "w")
    for tn, tc in TRIGS.items():
        H[(v,"all",tn)] = df.Filter(tc).Histo1D((f"{v}all{tn}","",len(e)-1,e), v, "w")
    for ci, cn in CATS.items():
        d = df.Filter(f"cat=={ci}")
        H[(v,cn,"den")] = d.Histo1D((f"{v}{cn}den","",len(e)-1,e), v, "w")
        for tn, tc in TRIGS.items():
            H[(v,cn,tn)] = d.Filter(tc).Histo1D((f"{v}{cn}{tn}","",len(e)-1,e), v, "w")
rep = df.Report()
out = {}
for v, e in EDGES.items():
    out[v] = {}
    for cn in ["all"] + list(CATS.values()):
        den = H[(v,cn,"den")]; rows = []
        for i in range(1, den.GetNbinsX()+1):
            N = den.GetBinContent(i); row = {"lo": e[i-1], "hi": e[i], "den": N}
            for tn in TRIGS:
                n = H[(v,cn,tn)].GetBinContent(i)
                eff = n/N if N > 0 else 0
                row[tn] = [eff, ((max(eff*(1-eff), 0.0)/N)**0.5) if N > 0 else 0.0]
            rows.append(row)
        out[v][cn] = rows
rep.Print()
json.dump(out, open(f"trigeff_bycat_{mass}.json","w"), indent=1)
print("wrote trigeff_bycat_%s.json" % mass)
