#include "TROOT.h"
#include <cstdarg>
#include <cmath>
#include <algorithm>
#include <initializer_list>

#include "/u/user/sako/ModHEEP/CMSSW_10_6_29/work/tdrstyle.C"
#include "/u/user/sako/ModHEEP/CMSSW_10_6_29/work/CMS_lumi.C"

typedef struct {
  float weight;
  float pt, eta, phi, en, et;
  int charge;
  float enSC, etSC, etaSC, phiSC, etaSeed, phiSeed, etaSCWidth, phiSCWidth;
  float full5x5_sigmaIetaIeta, full5x5_sigmaIphiIphi;
  float full5x5_E1x5, full5x5_E2x5, full5x5_E5x5, full5x5_hOverE, full5x5_r9;
  float dEtaIn, dPhiIn, dPhiSeed, dEtaEle, dPhiEle, dEtaSeed;
  float EseedOverP, EOverP;
  float ecalEn, ecalErr, trkErr, combErr, PFcombErr;
  float dr03TkSumPtHEEP, dr03EcalRecHitSumEt, dr03HcalDepth1TowerSumEt;
  float modTrkIso, modEcalIso;
  int lostHits, nValidHits, nValidPixelHits, GsfHits;
  float chi2, d0, d0Err, dxyErr, vz, dzErr, dxy, dz;
  float Gsfpt, Gsfeta, Gsfphi, GsfPtErr;
  int expectedMissingInnerHits;
  float convDist, convDcot, convRadius;
  int passConversionVeto, nbrem;
  float fbrem, fbremSC;
  float full5x5_e2x5Left, full5x5_e2x5Right, full5x5_e2x5Top, full5x5_e2x5Bottom;
  float full5x5_eLeft, full5x5_eRight, full5x5_eTop, full5x5_eBottom;
  float full5x5_eMax, full5x5_e2nd;
  float clus2ndMoment_sMaj, clus2ndMoment_sMin, clus2ndMoment_alpha;
  float dEtaSeedMiniAOD, dPhiInMiniAOD, sigIeIeMiniAOD;
  float union5x5dEtaIn, union5x5dPhiIn;
  float union5x5Energy, union5x5covIeIe, union5x5covIeIp, union5x5covIpIp;
  float union5x5covMaj, union5x5covMin;
  float alphaCalo;
  float GenPt, GenE;
  int u5x5numGood, u5x5numPoorReco, u5x5numOutOfTime, u5x5numFaultyHardware;
  int u5x5numNoisy, u5x5numPoorCalib, u5x5numSaturated, u5x5numLeadingEdgeRecovered;
  int u5x5NeighboursRecovered, u5x5numTowerRecovered, u5x5numDead, u5x5numKilled;
  int u5x5numTPSaturated, u5x5numL1SpikeFlag, u5x5numWeird, u5x5numDiWeird;
  int u5x5numHasSwitchToGain6, u5x5numHasSwitchToGain1, u5x5numUnknown;
  int u5x5numTPSaturatedAndTowerRecovered;
} ElectronStruct;

typedef struct {
  float weight;
  float pt, eta, phi;
  int lostHits, nValidHits, nValidPixelHits;
  float chi2, d0, d0Err, dxyErr, vz, dzErr, dxy, dz, ptErr;
  float deltaEtaSeedClusterAtVtx, deltaPhiSuperClusterAtVtx;
  float dPerpIn, normalizedDParaIn, alphaTrack;
} AddTrkStruct;

constexpr double pi = 3.14159265358979323846;

double deltaPhi(double phi1, double phi2) {
  double dphi = phi2 - phi1;

  if (dphi > pi)
    dphi -= 2.*pi;
  else if (dphi <= -pi)
    dphi += 2.*pi;

  return dphi;
}

double reduceRange(double x) {
  double o2pi = 1. / (2. * pi);
  if (std::abs(x) <= pi)
    return x;
  double n = std::round(x * o2pi);
  return x - n * 2. * pi;
}

double deltaR2(double eta1, double phi1,double eta2,double phi2) {
  return std::abs(eta1-eta2)*std::abs(eta1-eta2) + std::abs(deltaPhi(phi1,phi2))*std::abs(deltaPhi(phi1,phi2));
}

void compareMvaInputs(const std::string ang, const std::string etThres, const std::string EBEE, const std::string era) {
  TH1::SetDefaultSumw2();

  setTDRStyle();

  writeExtraText = true;            // if extra text
  extraText  = "#splitline{Simulation}{Work in progress}";  // default extra text is "Preliminary"
  lumi_sqrtS = "13 TeV";            // used with iPeriod = 0, e.g. for simulation-only plots (default is an empty string)

  if (era!="20UL16APV" && era!="20UL16" && era!="20UL17" && era!="20UL18") {
    std::cout << "check params!" << std::endl;
    throw;
  }

  if (era=="20UL16APV")
    lumi_sqrtS = "2016preVFP";
  else if (era=="20UL16")
    lumi_sqrtS = "2016postVFP";
  else if (era=="20UL17")
    lumi_sqrtS = "2017";
  else if (era=="20UL18")
    lumi_sqrtS = "2018";

  int iPeriod = 0; // 1=7TeV, 2=8TeV, 3=7+8TeV, 7=7+8+13TeV, 0=free form (uses lumi_sqrtS)
  int iPos = 11;

  if( iPos==0 )
    relPosX = 0.12;

  int W = 600;
  int H = 600;

  int H_ref = 600;
  int W_ref = 600;

  // references for T, B, L, R
  float T = 0.08*H_ref;
  float B = 0.12*H_ref;
  float L = 0.12*W_ref;
  float R = 0.04*W_ref;

  class sample {
  public:
    TFile* file;
    double xsec;
    int color;
    std::string name;

    // for bkg samples
    sample(TFile* afile, const double axsec, const int acolor) {
      file = afile;
      xsec = axsec;
      color = acolor;
      name = "";
    }

    // for sig samples
    sample(TFile* afile, const int acolor, const std::string& aname) {
      file = afile;
      color = acolor;
      xsec = 1.;
      name = aname;
    }
  };

  int nbins = 100;
  std::vector<sample> sigSamples;

  if (etThres=="Et1") {
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H250A1.root").c_str()),kSpring,"H250A1") );
  } else if (ang!="None"&&etThres=="Et2") {
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H750A1.root").c_str()),kSpring,"H750A1") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H2000A10.root").c_str()),kTeal-1,"H2000A10") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H750A10.root").c_str()),kBlue,"H750A10") );
  } else if (ang!="None"&&etThres=="") {
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H2000A1.root").c_str()),kRed,"H2000A1") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H750A1.root").c_str()),kOrange+7,"H750A1") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H250A1.root").c_str()),kSpring,"H250A1") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H2000A10.root").c_str()),kTeal-1,"H2000A10") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H750A10.root").c_str()),kAzure-2,"H750A10") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H250A10.root").c_str()),kBlue+2,"H250A10") );

    // if (era=="20UL18")
    //   sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_BuJpsiKee.root").c_str()),kGray,"Jpsi->ee") );
  } else if (ang=="None"&&etThres=="Et2") {
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H2000A1.root").c_str()),kRed,"H2000A1") );
    sigSamples.push_back( sample(TFile::Open(("MergedEleMva_"+era+"_H750A1.root").c_str()),kOrange+7,"H750A1") );
  } else {
    std::cout << "check params!" << std::endl;
    throw;
  }

  std::vector<sample> bkglist = {
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-0To70.root").c_str()),53870.0,kGreen-2), // kGreen),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-70To100.root").c_str()),1283.0,kGreen-2), // kGreen-7),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-100To200.root").c_str()),1244.0,kGreen-2), // kGreen+1),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-200To400.root").c_str()),337.8,kGreen-2), // kGreen-6),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-400To600.root").c_str()),44.93,kGreen-2), // kGreen-8),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-600To800.root").c_str()),11.19,kGreen-2), // kGreen-5),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-800To1200.root").c_str()),4.926,kGreen-2), // kGreen+2),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-1200To2500.root").c_str()),1.152,kGreen-2), // kGreen+3),
    sample(TFile::Open(("MergedEleMva_"+era+"_WJets_HT-2500ToInf.root").c_str()),0.02646,kGreen-2), // kGreen+4),

    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-0To70.root").c_str()),5379.0,kOrange), // kOrange),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-70To100.root").c_str()),140.0,kOrange), // kOrange-4),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-100To200.root").c_str()),139.2,kOrange), // kOrange+6),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-200To400.root").c_str()),38.4,kOrange), // kOrange-3),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-400To600.root").c_str()),5.174,kOrange), // kOrange+7),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-600To800.root").c_str()),1.258,kOrange), // kOrange-5),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-800To1200.root").c_str()),0.5598,kOrange), // kOrange+5),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-1200To2500.root").c_str()),0.1305,kOrange), // kOrange-6),
    sample(TFile::Open(("MergedEleMva_"+era+"_DY_HT-2500ToInf.root").c_str()),0.002997,kOrange), // kOrange+4),
    sample(TFile::Open(("MergedEleMva_"+era+"_TT.root").c_str()),471.7,kRed+1) // 831.76
  };

  auto retrieveTrees = [](const TString aname, std::vector<sample> list) {
    std::vector<TTree*> result;

    for (const auto& element : list)
      result.push_back((TTree*)(element.file)->Get(aname));

    return result;
  };

  auto retrieveHists = [](const TString aname, std::vector<sample> list) {
    std::vector<TH1D*> result;

    for (const auto& element : list)
      result.push_back((TH1D*)(element.file)->Get(aname));

    return result;
  };

  std::vector<TTree*> fakeTrees;
  std::vector<TTree*> fakeTrkTrees;

  std::vector<std::pair<TTree*,TTree*>> sigTreePair;

  if (ang!="None") {
    for (const auto& asample : sigSamples) {
      auto* elTree = (TTree*)asample.file->Get("mergedEleSigMvaInput/mergedEl1_elTree");
      auto* trkTree = (TTree*)asample.file->Get("mergedEleSigMvaInput/mergedEl1Trk_addTrkTree");
      sigTreePair.push_back(std::make_pair(elTree,trkTree));
    }

    fakeTrees = retrieveTrees("mergedEleBkgMvaInput/fake_elTree", bkglist);
    fakeTrkTrees = retrieveTrees("mergedEleBkgMvaInput/fakeTrk_addTrkTree", bkglist);
  } else if (ang=="None") {
    for (const auto& asample : sigSamples) {
      TTree* elTree = (TTree*)asample.file->Get("mergedEleSigMvaInput/mergedEl2_elTree");
      TTree* trkTree = nullptr;
      sigTreePair.push_back(std::make_pair(elTree,trkTree));
    }

    fakeTrees = retrieveTrees("mergedEleBkgMvaInput/bkg_elTree", bkglist);
  }

  auto fillElectrons = [&](TTree* tr, TTree* trkTree, TString postfix, std::vector<std::shared_ptr<TH2D>>& hist2Ds) -> std::vector<std::shared_ptr<TH1D>> {
    auto h_r9 = std::make_shared<TH1D>("R9_"+postfix,"R9;R9;nEle",nbins,0.,1.);
    auto h_detaInSeed = std::make_shared<TH1D>("dEtaInSeed_"+postfix,"#Delta#eta_{in}(seed);#Delta#eta_{in}^{seed};nEle",nbins,-0.005,0.005);
    auto h_dphiIn = std::make_shared<TH1D>("dPhiIn_"+postfix,"#Delta#phi_{in};#Delta#phi_{in};nEle",nbins,-0.02,0.02);
    auto h_EOP = std::make_shared<TH1D>("EoverP_"+postfix,"E/p;E/p;nEle",nbins,0.,10.);
    auto h_fbrem = std::make_shared<TH1D>("fbrem_"+postfix,"f_{brem};f_{brem};nEle",nbins,-1.,1.);

    auto h_sigIeIe = std::make_shared<TH1D>("sigIeIe_"+postfix,"#sigma_{i#eta i#eta};#sigma_{i#eta i#eta};nEle",nbins,0.,ang=="None" ? 0.015 : 0.05);
    auto h_E1x5E5x5 = std::make_shared<TH1D>("E1x5E5x5_"+postfix,"E1x5/E5x5;E1x5/E5x5;nEle",2.*nbins,0.,1.);
    auto h_sigIpIp = std::make_shared<TH1D>("sigIpIp_"+postfix,"#sigma_{i#phi i#phi};#sigma_{i#phi i#phi};nEle",nbins,0.,0.08);
    auto h_HoE = std::make_shared<TH1D>("HoE_"+postfix,"H/E;H/E;nEle",nbins,0.,0.1);
    auto h_HcalD1iso = std::make_shared<TH1D>("HcalD1iso_"+postfix,"HCAL depth1 iso;HcalD1iso;nEle",nbins,0.,20.);

    auto h_minmaxRatio = std::make_shared<TH1D>("minmaxRatio"+postfix,";sMin/sMaj;nEle",nbins,0.,1.);
    auto h_alphaSC = std::make_shared<TH1D>("alphaSC"+postfix,";alpha_{SC};nEle",nbins,-1.6,1.6);

    auto h_trackAlpha = std::make_shared<TH1D>("trackAlpha_"+postfix,";#alpha_{track};nEle",nbins,-1.6,1.6);

    auto h_union5x5covIeIe = std::make_shared<TH1D>("union5x5covIeIe_"+postfix,";#sigma_{i#eta i#eta}^{2};nEle",nbins,0.,2.);
    auto h_union5x5covIeIp = std::make_shared<TH1D>("union5x5covIeIp_"+postfix,";cov_{i#eta i#phi}/cov_{maj};nEle",nbins,-0.7,0.7);
    auto h_union5x5minmaxRatio = std::make_shared<TH1D>("union5x5minmaxRatio_"+postfix,";#sigma_{min}/#sigma_{Maj};nEle",nbins,0.,1.);
    auto h_alphaU5x5 = std::make_shared<TH1D>("alphaU5x5_"+postfix,";#alpha_{5x5};nEle",nbins,-1.6,1.6);

    auto h_detaInSeedMiniAOD = std::make_shared<TH1D>("dEtaInSeedMiniAOD_"+postfix,"#Delta#eta_{in}(seed);#Delta#eta_{in}(seed);nEle",nbins,-0.025,0.025);
    auto h_dphiInMiniAOD = std::make_shared<TH1D>("dPhiInMiniAOD_"+postfix,"#Delta#phi_{in};#Delta#phi_{in};nEle",nbins,-0.1,0.1);
    auto h_sigIeIeMiniAOD = std::make_shared<TH1D>("sigIeIeMiniAOD_"+postfix,"#sigma_{i#eta i#eta};#sigma_{i#eta i#eta};nEle",nbins,0.,0.05);

    auto h_union5x5detaIn = std::make_shared<TH1D>("union5x5dEtaIn_"+postfix,";#Delta#eta_{in}^{5x5};nEle",nbins,-0.05,0.05);
    auto h_union5x5dphiIn = std::make_shared<TH1D>("union5x5dPhiIn_"+postfix,";#Delta#phi_{in}^{5x5};nEle",nbins,-0.1,0.1);
    auto h_union5x5drIn = std::make_shared<TH1D>("h_union5x5drIn"+postfix,";#Delta R_{in}(u5x5);nEle",nbins,0.,0.05);
    auto h_union5x5EOP = std::make_shared<TH1D>("union5x5EoverP_"+postfix,"E/p(u5x5);E/p(u5x5);nEle",nbins,0.,10.);

    auto h_u5x5Et = std::make_shared<TH1D>("u5x5Et"+postfix,";E_{T u5x5};nEle",nbins,0.,1500.);
    auto h_Et = std::make_shared<TH1D>("Et"+postfix,";E_{T};nEle",nbins,0.,1500.);
    auto h_dr = std::make_shared<TH1D>("dr"+postfix,";#Delta R;nEle",nbins,0.,0.2);
    auto h_GenPt = std::make_shared<TH1D>("GenPt_"+postfix,";p_{T GEN};nEle",nbins,-10.,1490.);
    auto h_GenE = std::make_shared<TH1D>("GenE_"+postfix,";E_{GEN};nEle",nbins,-10.,1490.);
    auto h_GenPtRatio = std::make_shared<TH1D>("GenPtRatio_"+postfix,";E_{T reco}/p_{T GEN};nEle",nbins,-1.,3.);
    auto h_GenEratio = std::make_shared<TH1D>("GenEratio_"+postfix,";E_{reco}/E_{GEN};nEle",nbins,-1.,3.);

    auto h_dPerpIn = std::make_shared<TH1D>("dPerpIn"+postfix,";#Delta u_{in};nEle",nbins,-0.025,0.025);
    auto h_normDParaIn = std::make_shared<TH1D>("normDParaIn"+postfix,";#Delta v_{in}/#Delta R;nEle",nbins,-0.5,1.5);

    auto h_trackPtErr = std::make_shared<TH2D>("trackPtErr_"+postfix,";p_{T};dp_{T}/p_{T}",nbins,0.,1200.,nbins,0.,1.);
    auto h_eopErrEt = std::make_shared<TH2D>("eopErrEt_"+postfix,";E_{T};E/p error",nbins,0.,1200.,nbins,0.,1.);

    auto h_trackDEta = std::make_shared<TH1D>("trackDEta"+postfix,";#Delta#eta;nEle",nbins,-0.1,0.1);
    auto h_trackDPhi = std::make_shared<TH1D>("trackDPhi"+postfix,";#Delta#phi;nEle",nbins,-0.2,0.2);

    ElectronStruct elstruct;
    tr->SetBranchAddress("ElectronStruct",&elstruct);

    AddTrkStruct addtrkstruct;

    if (trkTree)
      trkTree->SetBranchAddress("AddTrkStruct",&addtrkstruct);

    for (int ievt = 0; ievt < tr->GetEntries(); ievt++) {
      tr->GetEntry(ievt);

      if (trkTree)
        trkTree->GetEntry(ievt);

      double weight = elstruct.weight/std::abs(elstruct.weight);

      if (EBEE=="EB") {
        if (std::abs(elstruct.etaSC) > 1.4442)
          continue;
      } else {
        if (std::abs(elstruct.etaSC) < 1.566)
          continue;
      }

      bool isEB = (std::abs(elstruct.etaSC) < 1.4442);

      const double eta1stGSF = -(elstruct.dEtaSeed - elstruct.etaSeed);
      const double u5x5Eta = elstruct.union5x5dEtaIn + eta1stGSF;
      const double u5x5Et = elstruct.union5x5Energy/std::cosh(u5x5Eta);

      if (etThres=="Et1") {
        if (isEB) {
          if (u5x5Et > 200 || u5x5Et < 50)
            continue;
        } else {
          if (u5x5Et > 150 || u5x5Et < 50)
            continue;
        }
      } else if (etThres=="Et2") {
        if (isEB) {
          if (u5x5Et < 200)
            continue;
        } else {
          if (u5x5Et < 150)
            continue;
        }
      } else if (etThres=="") {
        if (u5x5Et < 50)
          continue;
      } else {
        std::cout << "check Et threshold param!" << std::endl;
        throw;
      }

      if (elstruct.GenPt > 0.) {
        const double ratioU5x5 = u5x5Et/elstruct.GenPt;
        const double ratioSC = elstruct.etSC/elstruct.GenPt;

        if ( ratioU5x5 < 0.8 || ratioU5x5 > 1.2 )
          continue;

        // if ( ratioSC < 0.8 || ratioSC > 1.2 )
        //   continue;
      }

      h_r9->Fill(elstruct.full5x5_r9,weight);
      h_detaInSeed->Fill(elstruct.dEtaSeed,weight);
      h_dphiIn->Fill(elstruct.dPhiIn,weight);
      h_EOP->Fill(elstruct.EOverP,weight);
      h_fbrem->Fill(elstruct.fbrem,weight);
      h_E1x5E5x5->Fill(elstruct.full5x5_E1x5/elstruct.full5x5_E5x5,weight);
      h_sigIeIe->Fill(elstruct.full5x5_sigmaIetaIeta,weight);
      h_sigIpIp->Fill(elstruct.full5x5_sigmaIphiIphi,weight);
      h_HoE->Fill(elstruct.full5x5_hOverE,weight);
      h_HcalD1iso->Fill(elstruct.dr03HcalDepth1TowerSumEt,weight);

      h_minmaxRatio->Fill(elstruct.clus2ndMoment_sMin/elstruct.clus2ndMoment_sMaj,weight);
      h_alphaSC->Fill(elstruct.clus2ndMoment_alpha,weight);

      h_union5x5covIeIe->Fill(elstruct.union5x5covIeIe,weight);
      h_union5x5covIeIp->Fill(elstruct.union5x5covIeIp/elstruct.union5x5covMaj,weight);
      h_union5x5minmaxRatio->Fill(elstruct.union5x5covMin/elstruct.union5x5covMaj,weight);
      h_alphaU5x5->Fill(elstruct.alphaCalo,weight);

      h_detaInSeedMiniAOD->Fill(elstruct.dEtaSeedMiniAOD,weight);
      h_dphiInMiniAOD->Fill(elstruct.dPhiInMiniAOD,weight);
      h_sigIeIeMiniAOD->Fill(elstruct.sigIeIeMiniAOD,weight);

      h_union5x5detaIn->Fill(elstruct.union5x5dEtaIn,weight);
      h_union5x5dphiIn->Fill(elstruct.union5x5dPhiIn,weight);
      h_union5x5EOP->Fill(elstruct.union5x5Energy/elstruct.Gsfpt);

      const double drIn = std::hypot(elstruct.union5x5dEtaIn,elstruct.union5x5dPhiIn);
      h_union5x5drIn->Fill(drIn,weight);

      h_u5x5Et->Fill(u5x5Et,weight);
      h_Et->Fill(elstruct.et,weight);
      h_GenPt->Fill(elstruct.GenPt,weight);
      h_GenE->Fill(elstruct.GenE,weight);
      h_GenPtRatio->Fill(elstruct.GenPt < 0. ? -1. : u5x5Et/elstruct.GenPt,weight);
      h_GenEratio->Fill(elstruct.GenE < 0. ? -1. : elstruct.union5x5Energy/elstruct.GenE,weight);

      double eopErr = elstruct.EOverP*std::hypot( elstruct.ecalErr/elstruct.ecalEn, elstruct.GsfPtErr/elstruct.Gsfpt );

      h_eopErrEt->Fill(elstruct.et,eopErr,weight);
      h_trackPtErr->Fill(elstruct.Gsfpt,elstruct.GsfPtErr/elstruct.Gsfpt,weight); // GsfPtErr

      if (trkTree) {
        h_trackAlpha->Fill(addtrkstruct.alphaTrack,weight);

        h_dPerpIn->Fill( addtrkstruct.dPerpIn, weight );
        h_normDParaIn->Fill( addtrkstruct.normalizedDParaIn, weight );

        h_trackDEta->Fill(addtrkstruct.eta - elstruct.Gsfeta);
        h_trackDPhi->Fill( deltaPhi(addtrkstruct.phi, elstruct.Gsfphi) );

        h_dr->Fill( std::sqrt(deltaR2(addtrkstruct.eta,addtrkstruct.phi,elstruct.Gsfeta,elstruct.Gsfphi)) ,weight);
      }
    }

    std::vector<std::shared_ptr<TH1D>> hists;
    hists.push_back(std::move(h_detaInSeed));
    hists.push_back(std::move(h_dphiIn));
    hists.push_back(std::move(h_EOP));
    hists.push_back(std::move(h_E1x5E5x5));
    hists.push_back(std::move(h_sigIeIe));
    // hists.push_back(std::move(h_r9));
    // hists.push_back(std::move(h_fbrem));
    // hists.push_back(std::move(h_sigIpIp));
    // hists.push_back(std::move(h_HoE));
    // hists.push_back(std::move(h_HcalD1iso));
    // hists.push_back(std::move(h_minmaxRatio));
    // hists.push_back(std::move(h_alphaSC));

    // hists.push_back(std::move(h_alphaU5x5));
    // hists.push_back(std::move(h_union5x5detaIn));
    // hists.push_back(std::move(h_union5x5dphiIn));
    // hists.push_back(std::move(h_detaInSeedMiniAOD));
    // hists.push_back(std::move(h_dphiInMiniAOD));
    // hists.push_back(std::move(h_sigIeIeMiniAOD));
    // hists.push_back(std::move(h_union5x5EOP));

    // hists.push_back(std::move(h_union5x5covIeIe));
    // hists.push_back(std::move(h_union5x5covIeIp));
    // hists.push_back(std::move(h_union5x5minmaxRatio));

    // hists.push_back(std::move(h_union5x5drIn));

    // hists.push_back(std::move(h_u5x5Et));
    // hists.push_back(std::move(h_Et));
    // hists.push_back(std::move(h_GenPt));
    // hists.push_back(std::move(h_GenE));
    // hists.push_back(std::move(h_GenPtRatio));
    // hists.push_back(std::move(h_GenEratio));

    if (trkTree) {
      hists.push_back(std::move(h_trackAlpha));

      // hists.push_back(std::move(h_dPerpIn));
      hists.push_back(std::move(h_normDParaIn));

      // hists.push_back(std::move(h_trackDEta));
      // hists.push_back(std::move(h_trackDPhi));
      //
      // hists.push_back(std::move(h_dr));
    }

    // hist2Ds.push_back(std::move(h_trackPtErr));
    // hist2Ds.push_back(std::move(h_eopErrEt));

    return std::move(hists);
  };

  auto scaling = [&](std::vector<std::shared_ptr<TH1D>>& hists, std::vector<std::shared_ptr<TH2D>>& hist2Ds, int color, float xsec=0., double sumwgt=0.) {
    for (unsigned idx = 0; idx < hists.size(); idx++) {
      hists.at(idx)->Scale(xsec/sumwgt);
      hists.at(idx)->SetFillColor(color);
      hists.at(idx)->SetLineColor(color);
      hists.at(idx)->SetMarkerSize(0);
    }

    for (unsigned idx = 0; idx < hist2Ds.size(); idx++)
      hist2Ds.at(idx)->Scale(xsec/sumwgt);
  };

  auto stacking = [&](std::vector<std::unique_ptr<THStack>>& stacks, std::initializer_list<std::vector<std::shared_ptr<TH1D>>> aBkgHists) {
    for (unsigned idx = 0; idx < stacks.size(); idx++) {
      for (auto& element : aBkgHists)
        stacks.at(idx)->Add(element.at(idx).get());
    }
  };

  auto sumwgt_bkgs = retrieveHists("mergedEleBkgMvaInput/totWeightedSum", bkglist);

  std::vector<std::vector<std::shared_ptr<TH2D>>> sigHist2Ds;
  std::vector<std::vector<std::shared_ptr<TH1D>>> sigHists;

  for (unsigned idx = 0; idx < sigTreePair.size(); idx++) {
    std::vector<std::shared_ptr<TH2D>> asigHist2Ds;
    const auto apair = sigTreePair.at(idx);
    sigHists.push_back( fillElectrons(apair.first,apair.second,"sig"+std::to_string(idx),asigHist2Ds) );
    sigHist2Ds.push_back(asigHist2Ds);
  }

  std::vector<std::vector<std::shared_ptr<TH1D>>> histowner;
  std::vector<std::vector<std::shared_ptr<TH2D>>> hist2Downer;
  histowner.reserve(bkglist.size());
  hist2Downer.reserve(bkglist.size());

  for (unsigned idx = 0; idx < bkglist.size(); idx++) {
    std::string numstr = std::to_string(idx);
    std::vector<std::shared_ptr<TH1D>> hists;
    std::vector<std::shared_ptr<TH2D>> hists2Ds;

    if (ang!="None")
      hists = fillElectrons(fakeTrees.at(idx),fakeTrkTrees.at(idx),static_cast<std::string>("fake")+numstr,hists2Ds);
    else
      hists = fillElectrons(fakeTrees.at(idx),nullptr,static_cast<std::string>("bkg")+numstr,hists2Ds);

    histowner.emplace_back(std::move(hists));
    hist2Downer.push_back(std::move(hists2Ds));
  }

  for (unsigned idx = 0; idx < bkglist.size(); idx++)
    scaling(histowner.at(idx),
            hist2Downer.at(idx),
            bkglist.at(idx).color,
            bkglist.at(idx).xsec,
            sumwgt_bkgs.at(idx)->GetBinContent(1));

  std::vector<std::unique_ptr<THStack>> stacks;

  for (unsigned idx = 0; idx < histowner.front().size(); idx++)
    stacks.emplace_back(std::make_unique<THStack>(
      TString(histowner.front().at(idx)->GetName())+"_stack",
      TString(histowner.front().at(idx)->GetTitle())+";"+TString(histowner.front().at(idx)->GetXaxis()->GetTitle())+";"
    ));

  // manipulate stacking order here
  stacking(stacks,{
    histowner.at(18),

    histowner.at(17),
    histowner.at(16),
    histowner.at(15),
    histowner.at(14),
    histowner.at(13),
    histowner.at(12),
    histowner.at(11),
    histowner.at(10),
    histowner.at(9),

    histowner.at(8),
    histowner.at(7),
    histowner.at(6),
    histowner.at(5),
    histowner.at(4),
    histowner.at(3),
    histowner.at(2),
    histowner.at(1),
    histowner.at(0)
  });

  auto canvas = std::make_unique<TCanvas>("canvas","canvas",50,50,W,H);
  canvas->SetLogy();

  canvas->SetFillColor(0);
  canvas->SetBorderMode(0);
  canvas->SetFrameFillStyle(0);
  canvas->SetFrameBorderMode(0);
  canvas->SetLeftMargin( L/W );
  canvas->SetRightMargin( R/W );
  canvas->SetTopMargin( T/H );
  canvas->SetBottomMargin( B/H );
  canvas->SetTickx(0);
  canvas->SetTicky(0);

  // auto legend = std::make_unique<TLegend>(0.5,0.7,0.93,0.9);
  auto legend = std::make_unique<TLegend>(0.5,0.77,0.93,0.9);
  legend->SetNColumns(3);
  legend->SetBorderSize(0);

  legend->AddEntry(histowner.at(4).at(0).get(),"W");
  legend->AddEntry(histowner.at(11).at(0).get(),"DY");
  legend->AddEntry(histowner.at(18).at(0).get(),"TT");

  // loop over sig samples
  for (unsigned idx = 0; idx < sigSamples.size(); idx++)
    legend->AddEntry(sigHists.at(idx).at(0).get(),sigSamples.at(idx).name.c_str());

  // loop over hists
  for (unsigned idx = 0; idx < sigHists.front().size(); idx++) {
    double theMax = 0.;

    stacks.at(idx)->Draw("hist");
    stacks.at(idx)->GetXaxis()->SetLabelSize(0.03);
    stacks.at(idx)->GetYaxis()->SetLabelSize(0.03);
    stacks.at(idx)->GetXaxis()->SetTitleSize(0.05);
    theMax = std::max(stacks.at(idx)->GetMaximum(),theMax);

    auto* tmpHist = (TH1D*)stacks.at(idx)->GetHists()->At(0)->Clone();

    for (unsigned jdx = 1; jdx < stacks.at(idx)->GetHists()->GetSize(); jdx++)
      tmpHist->Add((TH1D*)stacks.at(idx)->GetHists()->At(jdx));

    double integral = tmpHist->Integral();

    // loop over sig samples
    for (unsigned iSig = 0; iSig < sigSamples.size(); iSig++) {
      const auto asigHists = sigHists.at(iSig);
      asigHists.at(idx)->Scale(integral/asigHists.at(idx)->Integral());
      asigHists.at(idx)->SetLineColor(sigSamples.at(iSig).color);
      asigHists.at(idx)->SetLineWidth(2);
      asigHists.at(idx)->SetMarkerSize(0);

      asigHists.at(idx)->Draw("hists&same");
      theMax = std::max(asigHists.at(idx)->GetMaximum(),theMax);
    }

    stacks.at(idx)->SetMaximum(10.*theMax);
    stacks.at(idx)->SetMinimum(10e-3*theMax);

    legend->Draw();

    canvas->Update();

    // writing the lumi information and the CMS "logo"
    CMS_lumi( canvas.get(), iPeriod, iPos );

    canvas->Update();
    canvas->RedrawAxis();
    canvas->GetFrame()->Draw();

    canvas->SaveAs(TString("MvaInputs/")+TString(ang)+TString(etThres)+TString(EBEE)+"_"+sigHists.front().at(idx)->GetName()+".pdf");
  } // histograms

  canvas->SetLogy(0);

  for (unsigned idx = 0; idx < sigHist2Ds.front().size(); idx++) {
    TH2D* bkghist2D = static_cast<TH2D*>(hist2Downer.front().at(idx).get()->Clone());

    for (unsigned jdx = 1; jdx < hist2Downer.size(); jdx++)
      bkghist2D->Add(hist2Downer.at(jdx).at(idx).get());

    bkghist2D->Draw("colz");

    for (unsigned iSig = 0; iSig < sigSamples.size(); iSig++) {
      const auto asigHist2Ds = sigHist2Ds.at(iSig).at(idx);
      asigHist2Ds->SetLineWidth(2);
      asigHist2Ds->SetLineColor(sigSamples.at(iSig).color);
      asigHist2Ds->SetContour(5);
      asigHist2Ds->Scale(bkghist2D->Integral()/asigHist2Ds->Integral());
      asigHist2Ds->Draw("cont3&same");
    }

    // writing the lumi information and the CMS "logo"
    CMS_lumi( canvas.get(), iPeriod, iPos );

    canvas->Update();
    canvas->RedrawAxis();
    canvas->GetFrame()->Draw();

    canvas->SaveAs(TString("MvaInputs/")+TString(ang)+TString(etThres)+TString(EBEE)+"_"+sigHist2Ds.front().at(idx)->GetName()+".png");
  }

  return;
}
