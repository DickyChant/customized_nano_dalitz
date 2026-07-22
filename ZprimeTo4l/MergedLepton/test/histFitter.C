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

  void fixSigmaFtoSigmaP(bool fix=true) { _fixSigmaFtoSigmaP= fix;}

  void setFitRange(double xMin,double xMax) { _xFitMin = xMin; _xFitMax = xMax; }

private:
  RooWorkspace *_work;
  std::string _histname_base;
  TFile *_fOut;
  double _nTotP, _nTotF;
  bool _useMinos;
  bool _fixSigmaFtoSigmaP;
  double _xFitMin,_xFitMax;
  int _nBins = 1000;
};

tnpFitter::tnpFitter(TH1 *hPass, TH1 *hFail, std::string histname  ) : _useMinos(false),_fixSigmaFtoSigmaP(false) {
  RooMsgService::instance().setGlobalKillBelow(RooFit::WARNING);
  _histname_base = histname;

  _nTotP = hPass->Integral();
  _nTotF = hFail->Integral();

  _work = new RooWorkspace("w") ;
  _work->factory("x[2.5,4.0]");

  RooDataHist rooPass("hPass","hPass",*_work->var("x"),hPass);
  RooDataHist rooFail("hFail","hFail",*_work->var("x"),hFail);
  _work->import(rooPass);
  _work->import(rooFail);
  _xFitMin = 2.5;
  _xFitMax = 4.0;
}

void tnpFitter::setWorkspace(std::vector<std::string> workspace) {
  for( unsigned icom = 0 ; icom < workspace.size(); ++icom ) {
    _work->factory(workspace[icom].c_str());
  }

  _work->var("x")->setBins(_nBins, "cache");

  _work->factory("FCONV::sigPass(x, Gaussian(x,3.1,0.01), sigResPass)");
  _work->factory("FCONV::sigFail(x, Gaussian(x,3.1,0.01), sigResFail)");
  _work->factory(TString::Format("nSigP[%f,0.5,%f]",_nTotP*0.1,_nTotP*1.5));
  _work->factory(TString::Format("nBkgP[%f,0.5,%f]",_nTotP*0.9,_nTotP*1.5));
  _work->factory(TString::Format("nSigF[%f,0.5,%f]",_nTotF*0.1,_nTotF*1.5));
  _work->factory(TString::Format("nBkgF[%f,0.5,%f]",_nTotF*0.9,_nTotF*1.5));
  _work->factory("SUM::pdfPass(nSigP*sigPass,nBkgP*bkgPass)");
  _work->factory("SUM::pdfFail(nSigF*sigFail,nBkgF*bkgFail)");
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

  if( _fixSigmaFtoSigmaP ) {
    _work->var("sigmaF")->setVal( _work->var("sigmaP")->getVal() );
    _work->var("sigmaF")->setConstant();
  }

  // _work->var("sigmaF")->setVal(_work->var("sigmaP")->getVal());
  // _work->var("sigmaF")->setRange(0.5* _work->var("sigmaP")->getVal(), 1.5* _work->var("sigmaP")->getVal());
  resFail = pdfFail->fitTo(*_work->data("hFail"), Minimizer("Minuit2", "MIGRAD"), Minos(_useMinos), Strategy(2), SumW2Error(kTRUE),Save(),Range("fitMassRange"));

  RooPlot *pPass = _work->var("x")->frame(_xFitMin,_xFitMax);
  RooPlot *pFail = _work->var("x")->frame(_xFitMin,_xFitMax);
  pPass->SetTitle("passing probe");
  pFail->SetTitle("failing probe");

  _work->data("hPass") ->plotOn( pPass );
  _work->pdf("pdfPass")->plotOn( pPass, LineColor(kRed) );
  _work->pdf("pdfPass")->plotOn( pPass, Components("bkgPass"),LineColor(kBlue),LineStyle(kDashed));
  _work->data("hPass") ->plotOn( pPass );

  _work->data("hFail") ->plotOn( pFail );
  _work->pdf("pdfFail")->plotOn( pFail, LineColor(kRed) );
  _work->pdf("pdfFail")->plotOn( pFail, Components("bkgFail"),LineColor(kBlue),LineStyle(kDashed));
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
}

/////// Stupid parameter dumper /////////
void tnpFitter::textParForCanvas(RooFitResult *resP, RooFitResult *resF,TPad *p) {
  double eff = -1;
  double e_eff = 0;

  RooRealVar *nSigP = _work->var("nSigP");
  RooRealVar *nSigF = _work->var("nSigF");

  double nP   = nSigP->getVal();
  double e_nP = nSigP->getError();
  double nF   = nSigF->getVal();
  double e_nF = nSigF->getError();
  double nTot = nP+nF;
  eff = nP / (nP+nF);
  e_eff = 1./(nTot*nTot) * sqrt( nP*nP* e_nF*e_nF + nF*nF * e_nP*e_nP );

  TPaveText *text1 = new TPaveText(0,0.8,1,1);
  text1->SetFillColor(0);
  text1->SetBorderSize(0);
  text1->SetTextAlign(12);

  text1->AddText(TString::Format("* fit status pass: %d, fail : %d",resP->status(),resF->status()));
  text1->AddText(TString::Format("* eff = %1.4f #pm %1.4f",eff,e_eff));

  // text->SetTextSize(0.06);

  // text->AddText("* Passing parameters");
  TPaveText *text = new TPaveText(0,0,1,0.8);
  text->SetFillColor(0);
  text->SetBorderSize(0);
  text->SetTextAlign(12);
  text->AddText("    --- parmeters " );
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
