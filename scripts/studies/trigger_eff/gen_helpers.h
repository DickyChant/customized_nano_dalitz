using namespace ROOT::VecOps;
RVec<int> genSel(const RVec<int>& pdg, const RVec<short>& mom, const RVec<int>& flags, int want){
  RVec<int> idx; for (size_t i=0;i<pdg.size();i++){ if (mom[i]<0) continue;
    if (std::abs(pdg[i])==want && pdg[mom[i]]==25 && ((flags[i]>>7)&1)) idx.push_back(i);} return idx; }
int nMatch(float eta, float phi, const RVec<float>& reta, const RVec<float>& rphi, const RVec<float>& rpt, float ptmin){
  int best=-1; float dmin=0.1; for(size_t j=0;j<reta.size();j++){ if(rpt[j]<ptmin) continue;
    float d=DeltaR(eta,reta[j],phi,rphi[j]); if(d<dmin){dmin=d;best=j;} } return best; }
