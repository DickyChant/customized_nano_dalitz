"""Trigger efficiency vs RECONSTRUCTED m(ee) and dR(e,e), UL18 signal MC.

The reco analogue of the generated pair is built per category:
  resolved (two distinct reco electrons) -> m and dR of the two reco electrons;
  merged, 2 GSF tracks in one electron  -> Electron_gsfDiTrkMass / Electron_gsfDeltaR;
  merged, only 1 GSF track              -> no reco observable exists (sentinel -999), excluded.
"""
import ROOT, glob, sys, json
ROOT.gROOT.SetBatch(True); ROOT.EnableImplicitMT(8)
mass = sys.argv[1] if len(sys.argv) > 1 else "M125"
files = sorted(glob.glob(f"/eos/uscms/store/user/cromerom/nanoDalitz_v3/*H*EEG_{mass}_*/*_{mass}_UL18_15X/*/*/*.root"))
print(len(files), "files")
ROOT.gInterpreter.Declare(r'''
using namespace ROOT::VecOps;
RVec<int> genSel(const RVec<int>& pdg, const RVec<short>& mom, const RVec<int>& flags, int want){
  RVec<int> idx; for (size_t i=0;i<pdg.size();i++){ if (mom[i]<0) continue;
    if (std::abs(pdg[i])==want && pdg[mom[i]]==25 && ((flags[i]>>7)&1)) idx.push_back(i);} return idx; }
int nMatch(float eta, float phi, const RVec<float>& reta, const RVec<float>& rphi, const RVec<float>& rpt, float ptmin){
  int best=-1; float dmin=0.1; for(size_t j=0;j<reta.size();j++){ if(rpt[j]<ptmin) continue;
    float d=DeltaR(eta,reta[j],phi,rphi[j]); if(d<dmin){dmin=d;best=j;} } return best; }
''')
df = ROOT.RDataFrame("Events", files)
df = (df.Define("w", "genWeight>0 ? 1.f : -1.f")
        .Define("gE", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 11)")
        .Define("gG", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 22)")
        .Filter("gE.size()==2 && gG.size()==1", "2 gen e + 1 gen pho")
        .Define("e1", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[0]],GenPart_eta[gE[0]],GenPart_phi[gE[0]],0.000511)")
        .Define("e2", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[1]],GenPart_eta[gE[1]],GenPart_phi[gE[1]],0.000511)")
        .Define("mgs_gen", "(float)(e1+e2).M()")
        .Define("dRee_gen", "(float)DeltaR(e1.Eta(),e2.Eta(),e1.Phi(),e2.Phi())")
        .Define("gEta", "GenPart_eta[gG[0]]").Define("gPhi", "GenPart_phi[gG[0]]")
        .Define("rPho", "nMatch(gEta,gPhi,Photon_eta,Photon_phi,Photon_pt,35.f)")
        .Define("rE1", "nMatch(e1.Eta(),e1.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rE2", "nMatch(e2.Eta(),e2.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rEleLeadPt", "float p=0; if(rE1>=0) p=std::max(p,Electron_pt[rE1]); if(rE2>=0) p=std::max(p,Electron_pt[rE2]); return p;")
        .Filter("rPho>=0 && rEleLeadPt>25", "reco photon + electron matched")
        .Define("category", "(rE1>=0&&rE2>=0) ? (rE1==rE2 ? 2 : 1) : 0")
        .Define("has2Gsf", "category==2 && Electron_gsfHasAddTrk[rE1]==1")
        # reco observables
        .Define("mgs", "if (category==1) { ROOT::Math::PtEtaPhiMVector a(Electron_pt[rE1],Electron_eta[rE1],Electron_phi[rE1],0.000511),"
                       "                                             b(Electron_pt[rE2],Electron_eta[rE2],Electron_phi[rE2],0.000511);"
                       "  return (float)(a+b).M(); }"
                       "else if (has2Gsf) return Electron_gsfDiTrkMass[rE1]; else return -999.f;")
        .Define("dRee", "if (category==1) return (float)DeltaR(Electron_eta[rE1],Electron_eta[rE2],Electron_phi[rE1],Electron_phi[rE2]);"
                        "else if (has2Gsf) return Electron_gsfDeltaR[rE1]; else return -999.f;")
        .Define("hasReco", "mgs > -1")
      )
trigs = ["HLT_DiEle27_WPTightCaloOnly_L1DoubleEG",
         "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90",
         "HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55"]
from array import array
edges = {"mgs": array('d',[0,1,2,3,4,5,6,7,8,9,10,15,20,30,40,50,60]),
         "dRee": array('d',[0,0.03,0.06,0.09,0.12,0.16,0.22,0.3,0.4,0.55,0.7,0.85,1])}
d = df.Filter("hasReco", "reco pair observable defined")
H = {}
for v, e in edges.items():
    H[(v,"den")] = d.Histo1D((f"{v}_den","",len(e)-1,e), v, "w")
    for t in trigs: H[(v,t)] = d.Filter(t).Histo1D((f"{v}_{t}","",len(e)-1,e), v, "w")
frac = {c: df.Filter(f"category=={c}").Sum("w") for c in (0,1,2)}
frac2g = df.Filter("has2Gsf").Sum("w"); tot = df.Sum("w"); nreco = d.Sum("w")
rep = df.Report()
out = {"reco": {}}
for v, e in edges.items():
    den = H[(v,"den")]; rows = []
    for i in range(1, den.GetNbinsX()+1):
        N = den.GetBinContent(i); row = {"lo": e[i-1], "hi": e[i], "den": N}
        for t in trigs:
            n = H[(v,t)].GetBinContent(i); eff = n/N if N > 0 else 0
            lo = ROOT.TEfficiency.ClopperPearson(int(round(N)), int(round(n)), 0.683, False) if N>0 else 0
            hi = ROOT.TEfficiency.ClopperPearson(int(round(N)), int(round(n)), 0.683, True) if N>0 else 0
            row[t] = [eff, eff-lo, hi-eff]
        rows.append(row)
    out["reco"][v] = rows
rep.Print()
T = tot.GetValue()
print("category fractions: resolved %.3f  merged %.3f  (merged with 2 GSF %.3f)  unmatched %.3f" %
      (frac[1].GetValue()/T, frac[2].GetValue()/T, frac2g.GetValue()/T, frac[0].GetValue()/T))
print("events with a reco pair observable: %.3f of the denominator" % (nreco.GetValue()/T))
out["fractions"] = {"resolved": frac[1].GetValue()/T, "merged": frac[2].GetValue()/T,
                    "merged2Gsf": frac2g.GetValue()/T, "hasReco": nreco.GetValue()/T}
json.dump(out, open(f"trigeff_reco_{mass}.json","w"), indent=1)
