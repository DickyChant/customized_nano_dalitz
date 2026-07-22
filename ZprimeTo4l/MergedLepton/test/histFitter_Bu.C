#include "RooDataHist.h"
#include "RooWorkspace.h"
#include "RooRealVar.h"
#include "RooAbsPdf.h"
#include "RooPlot.h"
#include "RooFitResult.h"
#include "TH1.h"
#include "TSystem.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TPaveText.h"

#include <vector>
#include <string>
#ifdef __CINT__
#pragma link C++ class std::vector<std::string>+;
#endif

using namespace RooFit;
using namespace std;

class tnpFitter {
public:
  tnpFitter( TH1 *hPass, TH1 *hFail, std::string histname  );
  ~tnpFitter(void) {if( _work != 0 ) delete _work; }

  void setWorkspace(std::vector<std::string>);
  void setOutputFile(TFile *fOut ) {_fOut = fOut;}
  void fits(std::string title = "");
  void useMinos(bool minos = true) {_useMinos = minos;}
  void textParForCanvas(RooFitResult *resP, RooFitResult *resF, TPad *p);

  void setFitRange(double xMin,double xMax) { _xFitMin = xMin; _xFitMax = xMax; }

  double meanRatio() { return meanRatio_; }
  double sigmaRatio() { return sigmaRatio_; }
  double meanRatioErr() { return meanRatioErr_; }
  double sigmaRatioErr() { return sigmaRatioErr_; }

private:
  RooWorkspace *_work;
  std::string _histname_base;
  TFile *_fOut;
  double _nTotP, _nTotF;
  bool _useMinos;
  double _xFitMin,_xFitMax;
  int _nBins = 100;
  double meanRatio_ = 1.;
  double sigmaRatio_ = 1.;
  double meanRatioErr_ = 0.;
  double sigmaRatioErr_ = 0.;
};

tnpFitter::tnpFitter(TH1 *hPass, TH1 *hFail, std::string histname  ) : _useMinos(false) {
  RooMsgService::instance().setGlobalKillBelow(RooFit::WARNING);
  _histname_base = histname;

  _nTotP = hPass->Integral();
  _nTotF = hFail->Integral();

  _work = new RooWorkspace("w") ;
  _work->factory("x[4.6,5.8]");

  RooDataHist rooPass("hPass","hPass",*_work->var("x"),hPass);
  RooDataHist rooFail("hFail","hFail",*_work->var("x"),hFail);
  _work->import(rooPass);
  _work->import(rooFail);
  _xFitMin = 4.6;
  _xFitMax = 5.8;
}

void tnpFitter::setWorkspace(std::vector<std::string> workspace) {
  for( unsigned icom = 0 ; icom < workspace.size(); ++icom ) {
    _work->factory(workspace[icom].c_str());
  }

  _work->var("x")->setBins(_nBins, "cache");

  _work->factory(TString::Format("nSigMC[%f,0.5,%f]",_nTotP*0.1,_nTotP*1.5));
  _work->factory(TString::Format("nBkgMC[%f,0.5,%f]",_nTotP*0.9,_nTotP*1.5));
  _work->factory(TString::Format("nSigData[%f,0.5,%f]",_nTotF*0.1,_nTotF*1.5));
  _work->factory(TString::Format("nBkgData[%f,0.5,%f]",_nTotF*0.9,_nTotF*1.5));
  _work->factory("SUM::pdfPass(nSigMC*sigResPass,nBkgMC*bkgPass)");
  _work->factory("SUM::pdfFail(nSigData*sigResFail,nBkgData*bkgFail)");
  _work->Print();			         
}

void tnpFitter::fits(string title) {
  cout << " title : " << title << endl;

  RooAbsPdf *pdfPass = _work->pdf("pdfPass");
  RooAbsPdf *pdfFail = _work->pdf("pdfFail");
  RooFitResult* resPass;  
  RooFitResult* resFail;

  /// FC: seems to be better to change the actual range than using a fitRange in the fit itself (???)
  /// FC: I don't know why but the integral is done over the full range in the fit not on the reduced range
  _work->var("x")->setRange(_xFitMin,_xFitMax);
  _work->var("x")->setRange("fitMassRange",_xFitMin,_xFitMax);
  resPass = pdfPass->fitTo(*_work->data("hPass"), Minimizer("Minuit2", "MIGRAD"), Minos(_useMinos), Strategy(2), SumW2Error(kTRUE),Save(),Range("fitMassRange"));

  _work->var("alphaData")->setVal( _work->var("alphaMC")->getVal() );
  _work->var("alphaData")->setConstant();
  _work->var("nData")->setVal( _work->var("nMC")->getVal() );
  _work->var("nData")->setConstant();

  resFail = pdfFail->fitTo(*_work->data("hFail"), Minimizer("Minuit2", "MIGRAD"), Minos(_useMinos), Strategy(2), SumW2Error(kTRUE),Save(),Range("fitMassRange"));

  RooPlot *pPass = _work->var("x")->frame(_xFitMin,_xFitMax);
  RooPlot *pFail = _work->var("x")->frame(_xFitMin,_xFitMax);
  pPass->SetTitle("MC");
  pFail->SetTitle("Data");

  _work->data("hPass") ->plotOn( pPass,Name("dataP"), MarkerSize(0.5) );
  _work->pdf("pdfPass")->plotOn( pPass,Name("sigP"), LineColor(kRed) );
  _work->pdf("pdfPass")->plotOn( pPass,Name("bkgP"), Components("bkgPass"),LineColor(kBlue),LineStyle(kDashed));
  _work->data("hPass") ->plotOn( pPass, MarkerSize(0.5) );

  _work->data("hFail") ->plotOn( pFail,Name("dataF") );
  _work->pdf("pdfFail")->plotOn( pFail,Name("sigF"), LineColor(kRed) );
  _work->pdf("pdfFail")->plotOn( pFail,Name("bkgF"), Components("bkgFail"),LineColor(kBlue),LineStyle(kDashed));
  _work->data("hFail") ->plotOn( pFail );

  TCanvas c("c","c",1100,450);
  c.Divide(3,1);
  TPad *padText = (TPad*)c.GetPad(1);
  textParForCanvas( resPass,resFail, padText );
  c.cd(2); pPass->Draw();
  c.cd(3); pFail->Draw();

  _fOut->cd();
  c.Write(TString::Format("%s_Canv",_histname_base.c_str()),TObject::kOverwrite);
  resPass->Write(TString::Format("%s_resP",_histname_base.c_str()),TObject::kOverwrite);
  resFail->Write(TString::Format("%s_resF",_histname_base.c_str()),TObject::kOverwrite);
  pPass->Write(TString::Format("%s_plotMC",_histname_base.c_str()),TObject::kOverwrite);
  pFail->Write(TString::Format("%s_plotData",_histname_base.c_str()),TObject::kOverwrite);
}

/////// Stupid parameter dumper /////////
void tnpFitter::textParForCanvas(RooFitResult *resP, RooFitResult *resF,TPad *p) {
  RooRealVar *meanMC = _work->var("meanMC");
  RooRealVar *meanData = _work->var("meanData");

  RooRealVar *sigmaMC = _work->var("sigmaMC");
  RooRealVar *sigmaData = _work->var("sigmaData");

  double mmc   = meanMC->getVal();
  double e_mmc = meanMC->getError();
  double mda   = meanData->getVal();
  double e_mda = meanData->getError();

  double smc   = sigmaMC->getVal();
  double e_smc = sigmaMC->getError();
  double sda   = sigmaData->getVal();
  double e_sda = sigmaData->getError();

  TPaveText *text1 = new TPaveText(0,0.75,1,1); // 0.9
  text1->SetFillColor(0);
  text1->SetBorderSize(0);
  text1->SetTextAlign(12);

  meanRatio_ = mmc/mda;
  sigmaRatio_ = sda/smc;
  meanRatioErr_ = mmc/mda*std::hypot(e_mmc/mmc,e_mda/mda);
  sigmaRatioErr_ = sda/smc*std::hypot(e_smc/smc,e_sda/sda);

  text1->AddText(TString::Format("* Fit status MC: %d, Data: %d",resP->status(),resF->status()));
  text1->AddText(TString::Format("* meanMC/meanData = %1.4f #pm %1.4f",meanRatio_,meanRatioErr_));
  text1->AddText(TString::Format("* sigmaData/sigmaMC = %1.4f #pm %1.4f",sigmaRatio_,sigmaRatioErr_));

  // text->SetTextSize(0.06);

  // text->AddText("* Passing parameters");
  TPaveText *text = new TPaveText(0,0,1,0.75);
  text->SetFillColor(0);
  text->SetBorderSize(0);
  text->SetTextAlign(12);
  text->AddText("    --- parameters " );
  RooArgList listParFinalP = resP->floatParsFinal();
  for( int ip = 0; ip < listParFinalP.getSize(); ip++ ) {
    TString vName = listParFinalP[ip].GetName();
    text->AddText(TString::Format("   - %s \t= %1.3f #pm %1.3f",
				  vName.Data(),
				  _work->var(vName)->getVal(),
				  _work->var(vName)->getError() ) );
  }

  // text->AddText("* Failing parameters");
  RooArgList listParFinalF = resF->floatParsFinal();
  for( int ip = 0; ip < listParFinalF.getSize(); ip++ ) {
    TString vName = listParFinalF[ip].GetName();
    text->AddText(TString::Format("   - %s \t= %1.3f #pm %1.3f",
				  vName.Data(),
				  _work->var(vName)->getVal(),
				  _work->var(vName)->getError() ) );
  }

  p->cd();
  text1->Draw();
  text->Draw();
}

