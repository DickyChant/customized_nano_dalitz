# Which requirement drives the HLT_Diphoton30_22_..._Mass90 inefficiency: R9Id, IsoCaloId, or Mass90?
# Per-leg info from TrigObj photon filter bits (UL18): bit14 = R9Id ET30 leg, bit15 = IsoCaloId ET30 leg.
# Both offline legs are required above 35 GeV so the ET30 threshold cannot fake an ID/iso failure.
import ROOT, glob, json
ROOT.gROOT.SetBatch(True); ROOT.EnableImplicitMT(8)
files = sorted(glob.glob("/eos/uscms/store/user/cromerom/nanoDalitz_v3/*H*EEG_M125_*/*_M125_UL18_15X/*/*/*.root"))
print(len(files), "files")
ROOT.gInterpreter.Declare(r'''
using namespace ROOT::VecOps;
RVec<int> genSel(const RVec<int>& pdg, const RVec<short>& mom, const RVec<int>& flags, int want){
  RVec<int> idx; for (size_t i=0;i<pdg.size();i++){ if (mom[i]<0) continue;
    if (std::abs(pdg[i])==want && pdg[mom[i]]==25 && ((flags[i]>>7)&1)) idx.push_back(i);} return idx; }
int nMatch(float eta, float phi, const RVec<float>& reta, const RVec<float>& rphi, const RVec<float>& rpt, float ptmin){
  int best=-1; float dmin=0.1; for(size_t j=0;j<reta.size();j++){ if(rpt[j]<ptmin) continue;
    float d=DeltaR(eta,reta[j],phi,rphi[j]); if(d<dmin){dmin=d;best=j;} } return best; }
bool objBit(float eta, float phi, const RVec<unsigned short>& id, const RVec<ULong64_t>& bits,
            const RVec<float>& teta, const RVec<float>& tphi, int bit){
  for (size_t i=0;i<id.size();i++){ if(id[i]!=22) continue;
    if (DeltaR(eta,teta[i],phi,tphi[i])<0.2 && ((bits[i]>>bit)&1)) return true; }
  return false; }
// invariant mass of the two highest-pT EG objects that passed either ET30 leg filter
float egPairMass(const RVec<unsigned short>& id, const RVec<ULong64_t>& bits, const RVec<float>& pt,
                 const RVec<float>& eta, const RVec<float>& phi){
  RVec<int> ok;
  for (size_t i=0;i<id.size();i++) if (id[i]==22 && ((((bits[i]>>14)&1)) || (((bits[i]>>15)&1)))) ok.push_back(i);
  if (ok.size()<2) return -1;
  std::sort(ok.begin(), ok.end(), [&](int a,int b){return pt[a]>pt[b];});
  ROOT::Math::PtEtaPhiMVector a(pt[ok[0]],eta[ok[0]],phi[ok[0]],0), b(pt[ok[1]],eta[ok[1]],phi[ok[1]],0);
  return (a+b).M(); }
''')
df = ROOT.RDataFrame("Events", files)
df = (df.Define("w", "genWeight>0 ? 1.f : -1.f")
        .Define("gE", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 11)")
        .Define("gG", "genSel(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags, 22)")
        .Filter("gE.size()==2 && gG.size()==1", "2 gen e + 1 gen pho")
        .Define("e1", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[0]],GenPart_eta[gE[0]],GenPart_phi[gE[0]],0.000511)")
        .Define("e2", "ROOT::Math::PtEtaPhiMVector(GenPart_pt[gE[1]],GenPart_eta[gE[1]],GenPart_phi[gE[1]],0.000511)")
        .Define("mgs", "(float)(e1+e2).M()").Define("dRee", "(float)DeltaR(e1.Eta(),e2.Eta(),e1.Phi(),e2.Phi())")
        .Define("gEta", "GenPart_eta[gG[0]]").Define("gPhi", "GenPart_phi[gG[0]]")
        .Define("rPho", "nMatch(gEta,gPhi,Photon_eta,Photon_phi,Photon_pt,35.f)")
        .Define("rE1", "nMatch(e1.Eta(),e1.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Define("rE2", "nMatch(e2.Eta(),e2.Phi(),Electron_eta,Electron_phi,Electron_pt,10.f)")
        .Filter("rPho>=0 && (rE1>=0 || rE2>=0)", "photon+electron matched")
        .Define("iE", "rE1>=0 && (rE2<0 || Electron_pt[rE1]>=Electron_pt[rE2]) ? rE1 : rE2")
        .Filter("Electron_pt[iE]>35 && Photon_pt[rPho]>35", "both legs > 35 GeV offline")
        .Define("pass", "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90")
        .Define("eEta","Electron_eta[iE]").Define("ePhi","Electron_phi[iE]")
        .Define("pEta","Photon_eta[rPho]").Define("pPhi","Photon_phi[rPho]")
        .Define("ee_R9",  "objBit(eEta,ePhi,TrigObj_id,TrigObj_filterBits,TrigObj_eta,TrigObj_phi,14)")
        .Define("ee_Iso", "objBit(eEta,ePhi,TrigObj_id,TrigObj_filterBits,TrigObj_eta,TrigObj_phi,15)")
        .Define("ph_R9",  "objBit(pEta,pPhi,TrigObj_id,TrigObj_filterBits,TrigObj_eta,TrigObj_phi,14)")
        .Define("ph_Iso", "objBit(pEta,pPhi,TrigObj_id,TrigObj_filterBits,TrigObj_eta,TrigObj_phi,15)")
        .Define("ee_any", "ee_R9 || ee_Iso").Define("ph_any", "ph_R9 || ph_Iso")
        .Define("legsOK", "ee_any && ph_any")
        .Define("mEG", "egPairMass(TrigObj_id,TrigObj_filterBits,TrigObj_pt,TrigObj_eta,TrigObj_phi)")
        .Define("massOK", "mEG>90")
        .Define("eleR9", "Electron_r9[iE]").Define("phoR9", "Photon_r9[rPho]")
        .Define("eleEcalIso", "Electron_ecalPFClusIso[iE]")
      )
bins = [(0,1),(1,2),(2,4),(4,6),(6,10),(10,15),(15,20),(20,30),(30,40),(40,50),(50,60)]
h={}
for lo,hi in bins:
    d = df.Filter(f"mgs>={lo} && mgs<{hi}")
    h[(lo,"N")]=d.Sum("w")
    for c in ["pass","ee_R9","ee_Iso","ee_any","ph_any","legsOK","massOK"]: h[(lo,c)]=d.Filter(c).Sum("w")
    h[(lo,"passGivenLegs")]=d.Filter("legsOK && pass").Sum("w")
    h[(lo,"massGivenLegs")]=d.Filter("legsOK && massOK").Sum("w")
    h[(lo,"R9")]=d.Mean("eleR9"); h[(lo,"iso")]=d.Mean("eleEcalIso"); h[(lo,"mEG")]=d.Mean("mEG")
print("\n              |------ ee-side leg ------|  pho  | both |  of events with both legs OK")
print("m_gs bin      N     pass   R9    Iso   any   any    legs |  m(EG,EG)>90   pass  | <R9_ee> <ecalIso_ee>")
out={}
for lo,hi in bins:
    N=h[(lo,"N")].GetValue(); L=h[(lo,"legsOK")].GetValue()
    g=lambda k: h[(lo,k)].GetValue()/N
    print("%2d-%2d %8.0f %6.3f %5.3f %5.3f %5.3f %5.3f %6.3f | %8.3f %8.3f | %6.2f %6.2f" % (
        lo,hi,N,g("pass"),g("ee_R9"),g("ee_Iso"),g("ee_any"),g("ph_any"),g("legsOK"),
        h[(lo,"massGivenLegs")].GetValue()/L if L else 0, h[(lo,"passGivenLegs")].GetValue()/L if L else 0,
        h[(lo,"R9")].GetValue(), h[(lo,"iso")].GetValue()))
    out[lo]={k:h[(lo,k)].GetValue() for k in ["N","pass","ee_R9","ee_Iso","ee_any","ph_any","legsOK","massOK","passGivenLegs","massGivenLegs"]}
json.dump(out, open("leg_decomp.json","w"), indent=1)
