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
        .Define("mgs", "(float)(e1+e2).M()")
        .Define("dRee", "(float)DeltaR(e1.Eta(),e2.Eta(),e1.Phi(),e2.Phi())")
        .Define("gPt", "GenPart_pt[gG[0]]").Define("gEta", "GenPart_eta[gG[0]]").Define("gPhi", "GenPart_phi[gG[0]]")
        .Define("eePt", "(float)(e1+e2).Pt()")
        # reco matching
        .Define("rPho", "nMatch(gEta,gPhi,Photon_eta,Photon_phi,Photon_pt,35.f)")
        .Define("rE1", "nMatch(e1.Eta(),e1.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rE2", "nMatch(e2.Eta(),e2.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rEleLeadPt", "float p=0; if(rE1>=0) p=std::max(p,Electron_pt[rE1]); if(rE2>=0) p=std::max(p,Electron_pt[rE2]); return p;")
        .Define("category", "(rE1>=0&&rE2>=0) ? (rE1==rE2 ? 2 : 1) : 0")  # 2=merged, 1=resolved, 0=missing
      )
dens = {
  "genAcc":  "gPt>35 && abs(gEta)<2.5 && abs(e1.Eta())<2.5 && abs(e2.Eta())<2.5 && eePt>35",
  "recoMatch": "rPho>=0 && rEleLeadPt>25",
}
trigs = ["HLT_DiEle27_WPTightCaloOnly_L1DoubleEG",
         "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90",
         "HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55"]
from array import array
edges = {"mgs": array('d',[0,1,2,3,4,5,6,7,8,9,10,15,20,30,40,50,60]),
         "dRee": array('d',[0,0.03,0.06,0.09,0.12,0.16,0.22,0.3,0.4,0.55,0.7,0.85,1])}
H = {}
for dn, dc in dens.items():
    d = df.Filter(dc, dn)
    for v, e in edges.items():
        H[(dn,v,"den")] = d.Histo1D((f"{dn}_{v}_den","",len(e)-1,e), v, "w")
        for t in trigs: H[(dn,v,t)] = d.Filter(t).Histo1D((f"{dn}_{v}_{t}","",len(e)-1,e), v, "w")
    H[(dn,"tot")] = d.Sum("w"); 
    for t in trigs: H[(dn,"tot",t)] = d.Filter(t).Sum("w")
    for c in (1,2): 
        H[(dn,"cat",c)] = d.Filter(f"category=={c}").Sum("w")
        for t in trigs: H[(dn,"cat",c,t)] = d.Filter(f"category=={c} && {t}").Sum("w")
rep = df.Report()
out = {"files": len(files)}
for dn in dens:
    out[dn] = {"total": {"den": H[(dn,"tot")].GetValue(), **{t: H[(dn,"tot",t)].GetValue() for t in trigs}},
               "cat": {c: {"den": H[(dn,"cat",c)].GetValue(), **{t: H[(dn,"cat",c,t)].GetValue() for t in trigs}} for c in (1,2)}}
    for v, e in edges.items():
        den = H[(dn,v,"den")]; rows = []
        for i in range(1, den.GetNbinsX()+1):
            row = {"lo": e[i-1], "hi": e[i], "den": den.GetBinContent(i)}
            for t in trigs:
                num = H[(dn,v,t)]
                gr = ROOT.TEfficiency.Bayesian if False else None
                n, N = num.GetBinContent(i), den.GetBinContent(i)
                eff = n/N if N>0 else 0
                lo = ROOT.TEfficiency.ClopperPearson(int(round(N)), int(round(n)), 0.683, False) if N>0 else 0
                hi = ROOT.TEfficiency.ClopperPearson(int(round(N)), int(round(n)), 0.683, True) if N>0 else 0
                row[t] = [eff, eff-lo, hi-eff]
            rows.append(row)
        out[dn][v] = rows
rep.Print()
json.dump(out, open(f"trigeff_{mass}.json","w"), indent=1)
for dn in dens:
    print("==", dn, {k: round(v/out[dn]['total']['den'],3) for k,v in out[dn]['total'].items()})
    for c in (1,2): print("   cat",c, {k: round(v/max(out[dn]['cat'][c]['den'],1),3) for k,v in out[dn]['cat'][c].items()})
    for v in edges:
        print("  ", v)
        for r in out[dn][v]: print("   [%5.2f,%5.2f) N=%7.0f " % (r['lo'],r['hi'],r['den']) + "  ".join("%.3f" % r[t][0] for t in trigs))
