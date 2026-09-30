"""Composition of the reco-level bins: which category and which pT populate the deep dip."""
import os, ROOT, glob
ROOT.gROOT.SetBatch(True); ROOT.EnableImplicitMT(8)
files = sorted(glob.glob("/eos/uscms/store/user/cromerom/nanoDalitz_v3/*H*EEG_M125_*/*_M125_UL18_15X/*/*/*.root"))
ROOT.gInterpreter.Declare(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_helpers.h")).read())
df = ROOT.RDataFrame("Events", files)
df = (df.Define("w", "genWeight>0 ? 1.f : -1.f")
        .Define("gE", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 11)")
        .Define("gG", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 22)")
        .Filter("gE.size()==2 && gG.size()==1")
        .Define("e1", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[0]],GenPart_eta[gE[0]],GenPart_phi[gE[0]],0.000511)")
        .Define("e2", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[1]],GenPart_eta[gE[1]],GenPart_phi[gE[1]],0.000511)")
        .Define("dRee_gen", "(float)ROOT::VecOps::DeltaR(e1.Eta(),e2.Eta(),e1.Phi(),e2.Phi())")
        .Define("gEta", "GenPart_eta[gG[0]]").Define("gPhi", "GenPart_phi[gG[0]]")
        .Define("rPho", "nMatch(gEta,gPhi,Photon_eta,Photon_phi,Photon_pt,35.f)")
        .Define("rE1", "nMatch(e1.Eta(),e1.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rE2", "nMatch(e2.Eta(),e2.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rEleLeadPt", "float p=0; if(rE1>=0) p=std::max(p,Electron_pt[rE1]); if(rE2>=0) p=std::max(p,Electron_pt[rE2]); return p;")
        .Filter("rPho>=0 && rEleLeadPt>25")
        .Define("category", "(rE1>=0&&rE2>=0) ? (rE1==rE2 ? 2 : 1) : 0")
        .Define("has2Gsf", "category==2 && Electron_gsfHasAddTrk[rE1]==1")
        .Define("dRee", "if (category==1) return (float)ROOT::VecOps::DeltaR(Electron_eta[rE1],Electron_eta[rE2],Electron_phi[rE1],Electron_phi[rE2]);"
                        "else if (has2Gsf) return Electron_gsfDeltaR[rE1]; else return -999.f;")
        .Filter("dRee > -1")
        .Define("isRes", "category==1").Define("elePt", "Electron_pt[rE1]")
        .Define("pass18", "HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55"))
bins = [(0,0.03),(0.03,0.06),(0.06,0.09),(0.09,0.12),(0.12,0.16),(0.16,0.22),(0.22,0.30),(0.30,0.40),(0.40,0.55)]
h = {}
for lo,hi in bins:
    d = df.Filter(f"dRee>={lo} && dRee<{hi}")
    h[(lo,'N')]=d.Sum("w"); h[(lo,'res')]=d.Filter("isRes").Sum("w")
    h[(lo,'pt')]=d.Mean("elePt"); h[(lo,'gdR')]=d.Mean("dRee_gen"); h[(lo,'p18')]=d.Filter("pass18").Sum("w")
print(f"{'reco dR bin':<14}{'N':>8}{'resolved':>10}{'<ele pT>':>10}{'<gen dR>':>10}{'eff 30_18':>11}")
for lo,hi in bins:
    N=h[(lo,'N')].GetValue()
    print(f"{lo:.2f}-{hi:.2f}   {N:8.0f}{100*h[(lo,'res')].GetValue()/N:9.1f}%{h[(lo,'pt')].GetValue():10.1f}{h[(lo,'gdR')].GetValue():10.3f}{h[(lo,'p18')].GetValue()/N:11.3f}")
