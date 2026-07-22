import ROOT
ROOT.gROOT.LoadMacro('./histFitter_Bu.C+')
ROOT.gROOT.SetBatch(1)

from ROOT import tnpFitter
import CMS_lumi, tdrstyle

import re
import math
import ctypes

import argparse
import os

import numpy as np

parser = argparse.ArgumentParser(description="Histogram fitter")
parser.add_argument("--sns",action="store_true",help="")
parser.add_argument("--doFit",action="store_true",help="perform fit")
parser.add_argument("--tdr",action="store_true",help="plot for paper")
args = parser.parse_args()

CMS_lumi.extraText = "Internal"

def histFitter( sample1, sample2, histname, tnpWorkspaceParam, tnpWorkspaceFunc, plotDir, lo, hi, prefix='mergedLeptonIDJpsiAnalyzer/', scale=1., smear=0. ):
    tnpWorkspace = []
    tnpWorkspace.extend(tnpWorkspaceParam)
    tnpWorkspace.extend(tnpWorkspaceFunc)

    ## init fitter
    infile1 = ROOT.TFile( sample1, "read")
    infile2 = ROOT.TFile( sample2, "read")

    hP = ROOT.TH1D('%sPass%s' % (prefix, histname),";GeV;",40,4.6,5.8)
    hF = ROOT.TH1D('%sFail%s' % (prefix, histname),";GeV;",40,4.6,5.8)

    atree = infile1.Get("mergedLeptonIDJpsiAnalyzer/BmesonTree")
    btree = infile2.Get("mergedLeptonIDJpsiAnalyzer/BmesonTree")

    upper = hi

    if hi==100.:
        upper = 13000.

    for idx, aEle in enumerate(atree):
        if aEle.u5x5Et > lo and aEle.u5x5Et < upper:
            if aEle.ptK > 3.5:
                lvecJpsi = ROOT.Math.PtEtaPhiEVector( math.sqrt(aEle.u5x5En*aEle.u5x5En-3.0969*3.0969)/math.cosh(aEle.etaJpsi), aEle.etaJpsi, aEle.phiJpsi, aEle.u5x5En )
                lvecK = ROOT.Math.PtEtaPhiMVector( aEle.ptK, aEle.etaK, aEle.phiK, 0.493677 )

                if aEle.passME:
                    if args.sns:
                        en = aEle.u5x5En + np.random.normal(0.,aEle.u5x5En*smear,1)
                        lvecJpsi = ROOT.Math.PtEtaPhiEVector( math.sqrt(en*en-3.0969*3.0969)/math.cosh(aEle.etaJpsi), aEle.etaJpsi, aEle.phiJpsi, en )

                    invM = (lvecJpsi+lvecK).M()
                    
                    hP.Fill(invM,aEle.wgt)

    for idx, aEle in enumerate(btree):
        if aEle.u5x5Et > lo and aEle.u5x5Et < upper:
            if aEle.ptK > 3.5:
                lvecJpsi = ROOT.Math.PtEtaPhiEVector( math.sqrt(aEle.u5x5En*aEle.u5x5En-3.0969*3.0969)/math.cosh(aEle.etaJpsi), aEle.etaJpsi, aEle.phiJpsi, aEle.u5x5En )
                lvecK = ROOT.Math.PtEtaPhiMVector( aEle.ptK, aEle.etaK, aEle.phiK, 0.493677 )

                if aEle.passME:
                    if args.sns:
                        en = aEle.u5x5En * scale
                        lvecJpsi = ROOT.Math.PtEtaPhiEVector( math.sqrt(en*en-3.0969*3.0969)/math.cosh(aEle.etaJpsi), aEle.etaJpsi, aEle.phiJpsi, en )

                    invM = (lvecJpsi+lvecK).M()

                    hF.Fill(invM,aEle.wgt)

    fitter = tnpFitter( hP, hF, (prefix+histname).replace('/','') )
    infile1.Close()
    infile2.Close()

    ## setup
    # fitter.useMinos()
    rootpath = sample1.replace('.root', '-%s.root' % (prefix+histname).replace('/','') )
    rootpath = plotDir + '/' + rootpath
    rootfile = ROOT.TFile(rootpath,'update')
    fitter.setOutputFile( rootfile )

    ### set workspace
    workspace = ROOT.vector("string")()
    for iw in tnpWorkspace:
        workspace.push_back(iw)
    fitter.setWorkspace( workspace )

    fitter.fits( (prefix+histname).replace('/','') )

    meanr = fitter.meanRatio()
    sigmar = fitter.sigmaRatio()
    meanrErr = fitter.meanRatioErr()
    sigmarErr = fitter.sigmaRatioErr()

    rootfile.Close()

    return meanr, sigmar, meanrErr, sigmarErr

def histPlotter( filename, histname, plotDir, prefix='mergedLeptonIDJpsiAnalyzer/' ):
    rootfile = ROOT.TFile(filename,"read")

    c = rootfile.Get( '%s_Canv' % (prefix+histname).replace('/','') )
    c.Print( '%s/%s.png' % (plotDir,(prefix+histname).replace('/','')))

def makeTGraphFromList( xlist, ylist, yerr ):
    output = ROOT.TGraphErrors(len(xlist))

    for ip in range(len(xlist)):
        output.SetPoint( ip, xlist[ip] , ylist[ip] )
        output.SetPointError( ip, 0., yerr[ip] )

    return output

def drawEff1D(xlist, ylist, yerr, nameout, xtitle, ytitle, xMin=0., xMax=0.):
    W = 600
    H = 600

    tdrstyle.setTDRStyle()

    canName = 'c'
    c = ROOT.TCanvas(canName,canName,50,50,W,H)
    c.SetTopMargin(0.055)
    c.SetBottomMargin(0.10)
    c.SetLeftMargin(0.12)

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptFit(0)

    agraph = makeTGraphFromList(xlist, ylist, yerr)
    agraph.SetMarkerColor( ROOT.kBlack )
    agraph.SetLineColor(   ROOT.kBlack )
    agraph.SetLineWidth(2) 

    agraph.GetHistogram().GetXaxis().SetTitleOffset(0.8)
    agraph.GetHistogram().GetXaxis().SetTitle(xtitle)
    agraph.GetHistogram().GetXaxis().SetTitleSize(0.04)
    agraph.GetHistogram().GetXaxis().SetLabelSize(0.03)

    agraph.GetHistogram().GetYaxis().SetTitle(ytitle)
    agraph.GetHistogram().GetYaxis().SetTitleOffset(1.6)
    agraph.GetHistogram().GetYaxis().SetTitleSize(0.04)
    agraph.GetHistogram().GetYaxis().SetLabelSize(0.03)
    agraph.SetTitle('')

    if xMin==0.:
        xMin = agraph.GetHistogram().GetXaxis().GetXmin()

    if xMax==0.:
        xMax = agraph.GetHistogram().GetXaxis().GetXmax()

    fitFunc = ROOT.TF1("fit","[0]*x+[1]",xMin,xMax)
    fitFunc.SetLineColor(ROOT.kGray+1)
    fitFunc.SetLineWidth(2)
    fitFunc.SetLineStyle(ROOT.kDashed)
    fitPtr = agraph.Fit(fitFunc,"S&R")

    agraph.Draw("AP")

    lineAtOne = ROOT.TLine(xMin,1,xMax,1)
    lineAtOne.SetLineStyle(ROOT.kDashed)
    lineAtOne.SetLineWidth(2)
    lineAtOne.Draw()

    c.cd()
    CMS_lumi.CMS_lumi(c, 5, 10)
    c.SaveAs(nameout+'.pdf')

def histPlotterTDR( filename, histname, plotDir, prefix='mergedLeptonIDJpsiAnalyzer/' ):
    rootfile = ROOT.TFile(filename,"read")

    pPass = rootfile.Get( '%s_plotData' % (prefix+histname).replace('/','') )
    pFail = rootfile.Get( '%s_plotMC' % (prefix+histname).replace('/','') )

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
    pPass.GetYaxis().SetRangeUser(0.,100.)
    pPass.GetXaxis().SetTitle("M [GeV]")
    pPass.SetMarkerSize(1.5)
    pPass.Draw()

    subpad.cd()
    pFail.SetMarkerSize(0.05)
    pFail.Draw()
    pFail.GetYaxis().SetRangeUser(0.,105.)
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

    legend.AddEntry("dataF","Data","P")
    legend.AddEntry("sigF","Crystal Ball signal fit","LP")
    legend.AddEntry("bkgF","Exponential background fit","LP")
    legend.Draw()

    ft = ROOT.TPaveText(0.66,0.85,0.83,0.91,"NDC");
    ft.SetBorderSize(0);
    ft.SetFillColor(0);
    ft.SetFillStyle(0);
    ft.AddText("Simulation");
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
    histname = "MergedEle_3trk_B_invM_u5x5"
    shortname = "res" # data or BuJpsiKee

    plotlist = [
        "JpsiPt30to100"
    ]

    binEdgeList = [30,100]

    tnpWorkspaceFunc = []
    tnpWorkspaceParam = []
    aplotDir = shortname + "/"

    tnpWorkspaceFunc = [
        "RooCBShape::sigResPass(x,meanMC,sigmaMC,alphaMC,nMC)",
        "RooCBShape::sigResFail(x,meanData,sigmaData,alphaData,nData)",
        "Exponential::bkgPass(x, kMC)",
        "Exponential::bkgFail(x, kData)"
    ]

    tnpWorkspaceParam = [
        "meanMC[5.28,5.18,5.38]","sigmaMC[0.05,0.01,0.2]","alphaMC[0.5,0.1,1.0]",'nMC[4,0.5,10]',
        "meanData[5.28,5.18,5.38]","sigmaData[0.05,0.01,0.2]","alphaData[0.5,0.1,1.0]",'nData[4,0.5,10]',
        "kMC[-1.,-2,-0.3]",
        "kData[-1.,-2,-0.3]"
    ]

    listscale = [1.01,1.008,1.005,1.002,1.0,0.998,0.995,0.992,0.99]
    listsmear = [0.015,0.02,0.022,0.024,0.025,0.026,0.028,0.03,0.035]
    listmeanr = []
    listmeanrErr = []
    listsigmar = []
    listsigmarErr = []

    if args.doFit and not args.tdr:
        if not os.path.exists(aplotDir):
            os.makedirs(aplotDir)

        for idx in range(len(plotlist)):
            aplot = plotlist[idx]
            aprefix = aplot
            histFitter("MergedEleJpsiAnalyzer_20UL18_BuJpsiKee.root","MergedEleJpsiAnalyzer_20UL18_data.root", histname, tnpWorkspaceParam, tnpWorkspaceFunc, aplotDir, binEdgeList[idx],binEdgeList[idx+1], aprefix )
            histPlotter( aplotDir + '/MergedEleJpsiAnalyzer_20UL18_BuJpsiKee-%s.root' % (aprefix+histname).replace('/',''), histname, aplotDir, aprefix )

        if args.sns:
            for idx in range(len(plotlist)):
                aplot = plotlist[idx]

                for scale in listscale:
                    tnpWorkspaceParam = [
                        "meanMC[5.28,5.18,5.38]","sigmaMC[0.053]","alphaMC[0.526]",'nMC[9.997]',
                        "meanData[5.28,5.18,5.38]","sigmaData[0.053]","alphaData[0.526]",'nData[9.997]',
                        "kMC[-0.3]",
                        "kData[-0.872]"
                    ]

                    aprefix = aplot + 'Scale' + str(scale)

                    meanr, sigmar, meanrErr, sigmarErr = histFitter("MergedEleJpsiAnalyzer_20UL18_BuJpsiKee.root","MergedEleJpsiAnalyzer_20UL18_data.root", histname, tnpWorkspaceParam, tnpWorkspaceFunc, aplotDir, binEdgeList[idx],binEdgeList[idx+1], aprefix , scale, 0.)
                    histPlotter( aplotDir + '/MergedEleJpsiAnalyzer_20UL18_BuJpsiKee-%s.root' % (aprefix+histname).replace('/',''), histname, aplotDir, aprefix )
                    listmeanr.append(meanr)
                    listmeanrErr.append(meanrErr)

                for smear in listsmear:
                    tnpWorkspaceParam = [
                        "meanMC[5.231]","sigmaMC[0.05,0.01,0.2]","alphaMC[0.526]",'nMC[9.997]',
                        "meanData[5.231]","sigmaData[0.05,0.01,0.2]","alphaData[0.526]",'nData[9.997]',
                        "kMC[-0.3]",
                        "kData[-0.872]"
                    ]

                    aprefix = aplot + 'Smear' + str(smear)

                    meanr, sigmar, meanrErr, sigmarErr = histFitter("MergedEleJpsiAnalyzer_20UL18_BuJpsiKee.root","MergedEleJpsiAnalyzer_20UL18_data.root", histname, tnpWorkspaceParam, tnpWorkspaceFunc, aplotDir, binEdgeList[idx],binEdgeList[idx+1], aprefix , 1., smear)
                    histPlotter( aplotDir + '/MergedEleJpsiAnalyzer_20UL18_BuJpsiKee-%s.root' % (aprefix+histname).replace('/',''), histname, aplotDir, aprefix )
                    listsigmar.append(sigmar)
                    listsigmarErr.append(sigmarErr)

            drawEff1D(listscale,listmeanr,listmeanrErr, "gridscale", "scale", "#mu_{MC}/#mu_{Data}")
            drawEff1D(listsmear,listsigmar,listsigmarErr, "gridsmear", "smearing", "#sigma_{Data}/#sigma_{MC}")
    elif args.tdr:
        aplot = "JpsiPt30to100tdr"
        aprefix = aplot
        histFitter("MergedEleJpsiAnalyzer_20UL18_BuJpsiKee.root","MergedEleJpsiAnalyzer_20UL18_data.root", histname, tnpWorkspaceParam, tnpWorkspaceFunc, aplotDir, 30, 100, aprefix )
        histPlotterTDR( aplotDir + '/MergedEleJpsiAnalyzer_20UL18_BuJpsiKee-%s.root' % (aprefix+histname).replace('/',''), histname, aplotDir, aprefix )

    print('Finished')
