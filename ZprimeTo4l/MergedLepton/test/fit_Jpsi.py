import ROOT
ROOT.gROOT.LoadMacro('./histFitter_Jpsi.C+')
ROOT.gROOT.LoadMacro('./RooCMSShape.cc+')
ROOT.gROOT.LoadMacro('./RooCBExGaussShape.cc+')
ROOT.gROOT.SetBatch(1)

from ROOT import tnpFitterJpsi
import CMS_lumi, tdrstyle

import re
import math
import ctypes

import argparse
import os

parser = argparse.ArgumentParser(description="Histogram fitter")
parser.add_argument("--nominal",action="store_true",help="nominal fit")
parser.add_argument("--altSig",action="store_true",help="altSig fit")
parser.add_argument("--altBkg",action="store_true",help="altBkg fit")
parser.add_argument("--doFit",action="store_true",help="perform fit")
parser.add_argument("--sumUp",action="store_true",help="sum-up efficiencies")
parser.add_argument("--tdr",action="store_true",help="plot for paper")
args = parser.parse_args()

class efficiency:
    def __init__(self,effData,errEffData,effMC,errEffMC,effAltBkg,effAltSig,low,high):
        self.effData = effData
        self.errEffData = errEffData
        self.effMC = effMC
        self.errEffMC = errEffMC
        self.effAltBkg = effAltBkg
        self.effAltSig = effAltSig
        self.low = low
        self.high = high

    def combineSyst(self):
        sysAltBkg = self.effAltBkg - self.effData
        sysAltSig = self.effAltSig - self.effData
        syst = sysAltBkg*sysAltBkg
        syst += sysAltSig*sysAltSig

        self.syst = math.sqrt(syst)

    def __str__(self):
        return '%2.3f\t%2.3f\t%2.3f\t%2.3f\t%2.3f\t%2.3f\t%2.3f\t%2.3f\t%2.3f' % (self.effData,self.errEffData,
                                                                                  self.effMC,self.errEffMC,
                                                                                  self.effAltBkg, self.effAltSig, self.low, self.high, self.syst )

def computeEffi(n1,n2,e1,e2):
    effout = []
    eff    = n1/(n1+n2)
    e_eff  = 1./(n1+n2)*math.sqrt(e1*e1*n2*n2+e2*e2*n1*n1)/(n1+n2)

    if e_eff < 0.001:
        e_eff = 0.001

    effout.append(eff)
    effout.append(e_eff)

    return effout

def readEff(aname, histname):
    rootfile = ROOT.TFile( aname, 'read' )

    fitresP = rootfile.Get( '%s_resP' % histname )
    fitresF = rootfile.Get( '%s_resF' % histname )

    nP = fitresP.floatParsFinal().find('nSigP').getVal()
    nF = fitresF.floatParsFinal().find('nSigF').getVal()
    eP = fitresP.floatParsFinal().find('nSigP').getError()
    eF = fitresF.floatParsFinal().find('nSigF').getError()
    rootfile.Close()

    return computeEffi(nP,nF,eP,eF)

def countEff(sample,histname,prefix='mergedLeptonIDJpsiAnalyzer/'):
    rootfile = ROOT.TFile( sample, 'read' )
    hP = rootfile.Get('%sPass%s' % (prefix, histname) )
    hF = rootfile.Get('%sFail%s' % (prefix, histname) )

    bin1 = 1
    bin2 = hP.GetNbinsX()
    eP = -1.
    eF = -1.
    nP = hP.IntegralAndError(bin1,bin2,ctypes.c_double(eP))
    nF = hF.IntegralAndError(bin1,bin2,ctypes.c_double(eF))
    rootfile.Close()

    return computeEffi(nP,nF,eP,eF)

def makeTGraphFromList( effList ):
    outData = ROOT.TGraphAsymmErrors(len(effList))
    outMC = ROOT.TGraphAsymmErrors(len(effList))
    outSF = ROOT.TGraphAsymmErrors(len(effList))

    for ip in range(len(effList)):
        point = effList[ip]
        errData = math.sqrt( point.errEffData*point.errEffData + point.syst*point.syst )

        errHigh = min( errData, 1. - point.effData )
        sferrLow = point.effData/point.effMC * math.hypot( errData/point.effData, point.errEffMC/point.effMC )
        sferrHigh = point.effData/point.effMC * math.hypot( errHigh/point.effData, point.errEffMC/point.effMC )

        outData.SetPoint(     ip, (point.low + point.high)/2. , point.effData )
        outData.SetPointError(ip, (point.high - point.low)/2., (point.high - point.low)/2., errData, errHigh )

        outMC.SetPoint(     ip, (point.low + point.high)/2. , point.effMC )
        outMC.SetPointError(ip, (point.high - point.low)/2., (point.high - point.low)/2. , point.errEffMC, min( point.errEffMC, 1. - point.effMC ) )

        outSF.SetPoint(     ip, (point.low + point.high)/2. , point.effData/point.effMC )
        outSF.SetPointError(ip, (point.high - point.low)/2., (point.high - point.low)/2., sferrLow, sferrHigh )

    return outData, outMC, outSF

def drawEff1D(effList, nameout):
    W = 600
    H = 600
    yUp = 0.45

    tdrstyle.setTDRStyle()

    canName = 'c'
    c = ROOT.TCanvas(canName,canName,50,50,W,H)
    c.SetTopMargin(0.055)
    c.SetBottomMargin(0.10)
    c.SetLeftMargin(0.12)

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptFit(0)

    p1 = ROOT.TPad( canName + '_up', canName + '_up', 0, yUp, 1,   1, 0,0,0)
    p2 = ROOT.TPad( canName + '_do', canName + '_do', 0,   0, 1, yUp, 0,0,0)
    p1.SetBottomMargin(0.0075)
    p1.SetTopMargin( c.GetTopMargin()*1./(1.-yUp) )
    p2.SetTopMargin(0.0075)
    p2.SetBottomMargin( c.GetBottomMargin()*1./yUp )
    p1.SetLeftMargin( c.GetLeftMargin() )
    p2.SetLeftMargin( c.GetLeftMargin() )

    p1.Draw()
    p2.Draw()

    leg = ROOT.TLegend(0.75,0.80,0.95 ,0.92)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetBorderSize(0)

    xMin = 20.
    xMax = 120.

    effiMin = 0.18
    effiMax = 1.35

    sfMin = 0.76
    sfMax = 1.24

    grBinsEffData, grBinsEffMC, grBinsSF = makeTGraphFromList(effList)

    grBinsEffMC.SetLineStyle( ROOT.kDashed )
    grBinsEffMC.SetLineColor( ROOT.kGray )
    grBinsEffMC.SetMarkerSize( 0 )
    grBinsEffMC.SetLineWidth( 2 )

    grBinsSF     .SetMarkerColor( ROOT.kBlack )
    grBinsSF     .SetLineColor(   ROOT.kBlack )
    grBinsSF     .SetLineWidth(2)
    grBinsEffData.SetMarkerColor( ROOT.kBlack )
    grBinsEffData.SetLineColor(   ROOT.kBlack )
    grBinsEffData.SetLineWidth(2)

    grBinsEffData.GetHistogram().SetMinimum(effiMin)
    grBinsEffData.GetHistogram().SetMaximum(effiMax)

    grBinsEffData.GetHistogram().GetXaxis().SetLimits(xMin,xMax)
    grBinsSF.GetHistogram()     .GetXaxis().SetLimits(xMin,xMax)
    grBinsSF.GetHistogram().SetMinimum(sfMin)
    grBinsSF.GetHistogram().SetMaximum(sfMax)

    grBinsSF.GetHistogram().GetXaxis().SetTitleOffset(1)
    grBinsSF.GetHistogram().GetXaxis().SetTitle("E_{T} [GeV]")
    grBinsSF.GetHistogram().GetXaxis().SetTitleSize(0.08)
    grBinsSF.GetHistogram().GetXaxis().SetLabelSize(0.06)

    grBinsSF.GetHistogram().GetYaxis().SetTitle("Data / MC ")
    grBinsSF.GetHistogram().GetYaxis().SetTitleOffset(0.8)
    grBinsSF.GetHistogram().GetYaxis().SetTitleSize(0.06)
    grBinsSF.GetHistogram().GetYaxis().SetLabelSize(0.06)
    grBinsSF.SetTitle('')

    grBinsEffData.GetHistogram().GetYaxis().SetTitleOffset(0.8)
    grBinsEffData.GetHistogram().GetYaxis().SetTitleSize(0.06)
    grBinsEffData.GetHistogram().GetYaxis().SetLabelSize(0.06)
    grBinsEffData.GetHistogram().GetYaxis().SetTitle("Efficiency")
    grBinsEffData.GetHistogram().GetYaxis().SetRangeUser( effiMin, effiMax )
    grBinsEffData.SetTitle('')

    leg.AddEntry( grBinsEffData, 'Data', "PL")
    leg.AddEntry( grBinsEffMC, 'MC', "PL")

    p1.cd()

    grBinsEffData.Draw("AP")
    grBinsEffMC.Draw("ez")

    p2.cd()

    fitFunc = ROOT.TF1("SF","[0]",20,120)
    fitFunc.SetLineColor(ROOT.kGray+1)
    fitFunc.SetLineWidth(2)
    fitFunc.SetLineStyle(ROOT.kDashed)
    fitPtr = grBinsSF.Fit(fitFunc,"S&R")

    xarr = [100.]
    yarr = [0.]
    xseq = ctypes.c_double*len(xarr)
    yseq = ctypes.c_double*len(yarr)
    cxarr = xseq(*xarr)
    cyarr = yseq(*yarr)
    fitPtr.GetConfidenceIntervals(1,1,0,cxarr,cyarr,0.95,False)

    textbox = ROOT.TPaveText(0.7,0.23,0.96,0.37,"NDC")
    textbox.SetBorderSize(0)
    textbox.SetFillStyle(3025)
    textbox.SetFillColor(0)

    textbox_pol = ROOT.TPaveText(0.13,0.23,0.55,0.37,"NDC")
    textbox_pol.SetBorderSize(0)
    textbox_pol.SetFillStyle(3025)
    textbox_pol.SetFillColor(0)

    textbox.AddText(r'#mu=%.3f, CI_{0.95}=#pm%.4g' % (fitFunc.GetParameter(0), cyarr[0]))
    lastText = textbox.GetListOfLines().Last()
    lastText.SetTextColor(ROOT.kGray+1)

    fitFuncPol = ROOT.TF1("SFpol","[0]*x+[1]",20,120)
    fitFuncPol.SetLineColor(ROOT.kGray+1)
    fitFuncPol.SetLineWidth(2)
    fitFuncPol.SetLineStyle(ROOT.kDashed)
    fitPtrPol = grBinsSF.Fit(fitFuncPol,"SREX0+")

    lastbinMCeff = (grBinsEffMC.GetY())[grBinsEffMC.GetN()-1]
    textbox_pol.AddText(r'%.4gE_{T}+%.3f #leq 1/eff_{MC} = %.4g' % (fitFuncPol.GetParameter(0), fitFuncPol.GetParameter(1), 1./lastbinMCeff))
    lastText = textbox_pol.GetListOfLines().Last()
    lastText.SetTextColor(ROOT.kGray+1)
    lastText.SetTextAlign(12)

    grBinsSF.Draw("AP")
    textbox.Draw()
    textbox_pol.Draw()

    lineAtOne = ROOT.TLine(xMin,1,xMax,1)
    lineAtOne.SetLineStyle(ROOT.kSolid)
    lineAtOne.SetLineWidth(1)
    lineAtOne.Draw()

    c.cd()

    leg.Draw()
    CMS_lumi.CMS_lumi(c, 5, 10)

    c.SaveAs(nameout+'.pdf')

def histFitter( sample, histname, tnpWorkspaceParam, tnpWorkspaceFunc, plotDir, lo, hi, prefix='mergedLeptonIDJpsiAnalyzer/' ):

    tnpWorkspace = []
    tnpWorkspace.extend(tnpWorkspaceParam)
    tnpWorkspace.extend(tnpWorkspaceFunc)

    ## init fitter
    infile = ROOT.TFile( sample, "read")

    hP = ROOT.TH1D('%sPass%s' % (prefix, histname),";GeV;",50,2.5,4.)
    hF = ROOT.TH1D('%sFail%s' % (prefix, histname),";GeV;",50,2.5,4.)

    atree = infile.Get("mergedLeptonIDJpsiAnalyzer/dielTree")

    upper = hi

    if hi==120.:
        upper = 13000.

    for idx, aEle in enumerate(atree):
        if aEle.u5x5Et > lo and aEle.u5x5Et < upper:
            if aEle.passME:
                hP.Fill(aEle.invM,aEle.wgt)
            else:
                hF.Fill(aEle.invM,aEle.wgt)

    # hP = infile.Get('%sPass%s' % (prefix, histname) )
    # hF = infile.Get('%sFail%s' % (prefix, histname) )

    # hP.Rebin(5)
    # hF.Rebin(5)

    fitter = tnpFitterJpsi( hP, hF, (prefix+histname).replace('/','') )
    infile.Close()

    ## setup
    # fitter.useMinos()
    rootpath = sample.replace('.root', '-%s.root' % (prefix+histname).replace('/','') )
    rootpath = plotDir + '/' + rootpath
    rootfile = ROOT.TFile(rootpath,'update')
    fitter.setOutputFile( rootfile )

    ### set workspace
    workspace = ROOT.vector("string")()
    for iw in tnpWorkspace:
        workspace.push_back(iw)
    fitter.setWorkspace( workspace )

    fitter.fits( (prefix+histname).replace('/','') )
    rootfile.Close()

def histPlotter( filename, histname, plotDir, prefix='mergedLeptonIDJpsiAnalyzer/' ):
    rootfile = ROOT.TFile(filename,"read")

    c = rootfile.Get( '%s_Canv' % (prefix+histname).replace('/','') )
    c.Print( '%s/%s.png' % (plotDir,(prefix+histname).replace('/','')))

def histPlotterTDR( filename, histname, plotDir, prefix='mergedLeptonIDJpsiAnalyzer/' ):
    rootfile = ROOT.TFile(filename,"read")

    pPass = rootfile.Get( '%s_plotP' % (prefix+histname).replace('/','') )
    pFail = rootfile.Get( '%s_plotF' % (prefix+histname).replace('/','') )

    #set the tdr style
    tdrstyle.setTDRStyle()

    #change the CMS_lumi variables (see CMS_lumi.py)
    CMS_lumi.writeExtraText = 1
    CMS_lumi.extraText = "Work in progress"

    CMS_lumi.lumi_sqrtS = "41.69 fb^{-1}"

    iPos = 11
    CMS_lumi.relPosX = 0.05

    H_ref = 800;
    W_ref = 800;
    W = W_ref
    H = H_ref

    iPeriod = 0

    # references for T, B, L, R
    T = 0.08*H_ref
    B = 0.12*H_ref
    L = 0.12*W_ref
    R = 0.04*W_ref

    canvas = ROOT.TCanvas("c","c",50,50,W,H)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetLeftMargin( L/W )
    canvas.SetRightMargin( R/W )
    canvas.SetTopMargin( T/H )
    canvas.SetBottomMargin( B/H )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.cd()

    subpad = ROOT.TPad("pad","pad",0.6,0.6,0.965,0.91)
    subpad.SetFillColor(0);
    subpad.SetBorderMode(0);
    subpad.SetFrameFillStyle(0);
    subpad.SetFrameBorderMode(0);
    subpad.SetLeftMargin( 0.15 );
    subpad.SetRightMargin( 0.05 );
    subpad.SetTopMargin( 0 );
    subpad.SetBottomMargin( 0.1 );
    subpad.SetTickx(0);
    subpad.SetTicky(0);

    canvas.cd()
    pPass.GetYaxis().SetRangeUser(0.,550.)
    pPass.GetXaxis().SetTitle("M [GeV]")
    pPass.SetMarkerSize(1.5)
    pPass.Draw()

    subpad.cd()
    pFail.SetMarkerSize(0.05)
    pFail.Draw()
    pFail.GetXaxis().SetTitle("M [GeV]")
    pFail.GetXaxis().SetTitleSize(0.05)
    pFail.GetXaxis().SetLabelSize(0.05)
    pFail.GetYaxis().SetLabelSize(0.05)
    pFail.GetYaxis().SetTitle("")

    canvas.Update()
    canvas.cd()
    subpad.Draw()

    # legend = ROOT.TLegend(0.5,0.75,0.95,0.9)
    legend = ROOT.TLegend(L/W+0.01,B/H+0.01,0.55,0.3)
    legend.SetBorderSize(0);

    legend.AddEntry("dataP","Data","P")
    legend.AddEntry("sigP","Gaussian signal fit","LP")
    legend.AddEntry("bkgP","Exponential background fit","LP")
    legend.Draw()

    pt = ROOT.TPaveText(0.15,0.28,0.4,0.36,"NDC");
    pt.SetBorderSize(0);
    pt.SetFillColor(0);
    pt.SetFillStyle(0);
    pt.AddText("Passing region");
    pt.Draw();

    ft = ROOT.TPaveText(0.66,0.62,0.83,0.7,"NDC");
    ft.SetBorderSize(0);
    ft.SetFillColor(0);
    ft.SetFillStyle(0);
    ft.AddText("Failing region");
    ft.Draw();

    #draw the lumi text on the canvas
    CMS_lumi.CMS_lumi(canvas, iPeriod, iPos)
    canvas.cd()
    canvas.Update()
    canvas.RedrawAxis()
    frame = canvas.GetFrame()
    frame.Draw()

    canvas.SaveAs( '%s/%s.pdf' % (plotDir,(prefix+histname).replace('/','')))

if __name__ == "__main__":
    histname = "MergedEle_2trk_diel_invM"
    prefix = "mergedLeptonIDJpsiAnalyzer/"
    shortname = "data" # data or BuJpsiKee

    plotlist = [
        "JpsiPt20to25",
        "JpsiPt25to30",
        "JpsiPt30to35",
        "JpsiPt35to40",
        "JpsiPt40to50",
        "JpsiPt50to60",
        "JpsiPt60toInf"
    ]

    binEdgeList = [20,25,30,35,40,50,60,120]

    tnpWorkspaceFunc = []
    tnpWorkspaceParam = []
    aplotDir = shortname + "/"

    if args.altSig:
        tnpWorkspaceFunc = [
            "RooCBExGaussShape::sigResPass(x,meanP,expr('sqrt(sigmaP*sigmaP+sosP*sosP)',{sigmaP,sosP}),alphasP,nP, expr('sqrt(sigmaP_2*sigmaP_2+sosP*sosP)',{sigmaP_2,sosP}),0.)",
            "RooCBExGaussShape::sigResFail(x,meanF,expr('sqrt(sigmaF*sigmaF+sosF*sosF)',{sigmaF,sosF}),alphasF,nF, expr('sqrt(sigmaF_2*sigmaF_2+sosF*sosF)',{sigmaF_2,sosF}),0.)",
            "Exponential::bkgPass(x, alphaP)",
            "Exponential::bkgFail(x, alphaF)"
        ]

        tnpWorkspaceParam = [
            "meanP[0.1,-0.12,0.12]","sigmaP[0.03,0.012,0.1]","alphasP[0.2,0.1,0.5]",'nP[3,0,5]',"sigmaP_2[0.05,0.012,0.1]","sosP[0.001,0.001,0.1]",
            "meanF[0.1,-0.12,0.12]","sigmaF[0.03,0.012,0.1]","alphasF[0.2,0.1,0.5]",'nF[3,0,5]',"sigmaF_2[0.05,0.012,0.1]","sosF[0.001,0.001,0.1]",
            "alphaP[-1.,-2,-0.65]",
            "alphaF[-1.,-2,-0.65]"
        ]

        aplotDir += 'altSig'
    elif args.nominal:
        tnpWorkspaceFunc = [
            "Gaussian::sigResPass(x,meanP,sigmaP)",
            "Gaussian::sigResFail(x,meanF,sigmaF)",
            "Exponential::bkgPass(x, alphaP)",
            "Exponential::bkgFail(x, alphaF)"
        ]

        tnpWorkspaceParam = [
            "meanP[0.1,-0.15,0.15]","sigmaP[0.06,0.025,0.15]",
            "meanF[0.1,-0.15,0.15]","sigmaF[0.06,0.025,0.12]",
            "alphaP[-1.,-2,-0.65]",
            "alphaF[-1.,-2,-0.65]"
        ]

        aplotDir += 'nominal'
    elif args.altBkg:
        tnpWorkspaceFunc = [
            "Gaussian::sigResPass(x,meanP,sigmaP)",
            "Gaussian::sigResFail(x,meanF,sigmaF)",
            "RooCMSShape::bkgPass(x, acmsP, betaP, gammaP, peakP)",
            "RooCMSShape::bkgFail(x, acmsF, betaF, gammaF, peakF)"
        ]

        tnpWorkspaceParam = [
            "meanP[0.1,-0.15,0.15]","sigmaP[0.06,0.025,0.15]",
            "meanF[0.1,-0.15,0.15]","sigmaF[0.06,0.025,0.15]",
            "acmsP[2.,5.,5.]","betaP[0.05,0.01,0.1]","gammaP[1.0, -2, 2]","peakP[3.1]",
            "acmsF[2.,5.,5.]","betaF[0.05,0.01,0.1]","gammaF[1.0, -2, 2]","peakF[3.1]"
        ]

        aplotDir += 'altBkg'
    else:
        pass

    if args.doFit and not args.tdr:
        if not os.path.exists(aplotDir):
            os.makedirs(aplotDir)

        for idx in range(len(plotlist)):
            aplot = plotlist[idx]
            aprefix = prefix + aplot
            histFitter( "MergedEleJpsiAnalyzer_20UL18_%s.root" % shortname, histname, tnpWorkspaceParam, tnpWorkspaceFunc, aplotDir, binEdgeList[idx],binEdgeList[idx+1], aprefix )
            histPlotter( aplotDir + '/MergedEleJpsiAnalyzer_20UL18_%s-%s.root' % (shortname, (aprefix+histname).replace('/','')), histname, aplotDir, aprefix )
    elif args.tdr:
        aplot = "JpsiPt50toInf"
        aprefix = prefix + aplot
        histFitter( "MergedEleJpsiAnalyzer_20UL18_%s.root" % shortname, histname, tnpWorkspaceParam, tnpWorkspaceFunc, aplotDir, 50, 120, aprefix )
        histPlotterTDR( aplotDir + '/MergedEleJpsiAnalyzer_20UL18_%s-%s.root' % (shortname, (aprefix+histname).replace('/','')), histname, aplotDir, aprefix )
    elif args.sumUp:
        effList = []

        for idx in range(len(plotlist)):
            aplot = plotlist[idx]
            aprefix = prefix + aplot

            effNominal = readEff( "data/nominal" + '/MergedEleJpsiAnalyzer_20UL18_%s-%s.root' % ("data", (aprefix+histname).replace('/','')), (aprefix+histname).replace('/','') )
            effAltSig = readEff( "data/altSig" + '/MergedEleJpsiAnalyzer_20UL18_%s-%s.root' % ("data", (aprefix+histname).replace('/','')), (aprefix+histname).replace('/','') )
            effAltBkg = readEff( "data/altBkg" + '/MergedEleJpsiAnalyzer_20UL18_%s-%s.root' % ("data", (aprefix+histname).replace('/','')), (aprefix+histname).replace('/','') )
            effMC = readEff( "BuJpsiKee/nominal" + '/MergedEleJpsiAnalyzer_20UL18_%s-%s.root' % ("BuJpsiKee", (aprefix+histname).replace('/','')), (aprefix+histname).replace('/','') )
                    # countEff( "MergedEleJpsiAnalyzer_20UL18_%s.root" % "BuJpsiKee", histname, aprefix )

            aeff = efficiency(effNominal[0],effNominal[1],effMC[0],effMC[1],effAltBkg[0],effAltSig[0],binEdgeList[idx],binEdgeList[idx+1])
            aeff.combineSyst()

            effList.append( aeff )

            print(aeff)

        drawEff1D(effList, 'SFvsEt')

    print('Finished')
