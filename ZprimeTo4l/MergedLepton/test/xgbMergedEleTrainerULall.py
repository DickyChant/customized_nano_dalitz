#!/usr/bin/env python3

import ROOT
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
import hyperopt
import math
from array import array
import argparse
import os

import xgbPreprocess as zprep
import xgbVis as zvis

parser = argparse.ArgumentParser(description="BDT training for merged electrons")
parser.add_argument("--det",dest="det",type=str,help="detector (EB/EE)")
parser.add_argument("--ang",dest="angle",type=str,help="opening angle (''/None)")
parser.add_argument("--et",dest="et",type=str,help="Et range (''/Et1/Et2)")

args = parser.parse_args()

# choose the right signal model for relevant phase spaces
sigSamples1 = []
sigSamples2 = []
sigSamples3 = []
sigSamples4 = []
etThres = 50.

def addSigMC(era):
    sigSamples = []
    sigSamples.append(zprep.sample("data/MergedEleMva_"+era+"_H2000A1.root","X2000Y1",ROOT.kOrange))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+era+"_H750A1.root","X750Y1",ROOT.kSpring+2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+era+"_H250A1.root","X250Y1",ROOT.kTeal+2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+era+"_H2000A10.root","X2000Y10",ROOT.kCyan+2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+era+"_H750A10.root","X750Y10",ROOT.kAzure-2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+era+"_H250A10.root","X250Y10",ROOT.kBlue+2))

    return sigSamples


if args.angle=="None" and args.et=="Et2":
    sigSamples1.append(zprep.sample("data/MergedEleMva_20UL16APV_H750A1.root","X750Y1",ROOT.kTeal+2))
    sigSamples2.append(zprep.sample("data/MergedEleMva_20UL16_H750A1.root","X750Y1",ROOT.kTeal+2))
    sigSamples3.append(zprep.sample("data/MergedEleMva_20UL17_H750A1.root","X750Y1",ROOT.kTeal+2))
    sigSamples4.append(zprep.sample("data/MergedEleMva_20UL18_H750A1.root","X750Y1",ROOT.kTeal+2))

    sigSamples1.append(zprep.sample("data/MergedEleMva_20UL16APV_H2000A1.root","X2000Y1",ROOT.kOrange))
    sigSamples2.append(zprep.sample("data/MergedEleMva_20UL16_H2000A1.root","X2000Y1",ROOT.kOrange))
    sigSamples3.append(zprep.sample("data/MergedEleMva_20UL17_H2000A1.root","X2000Y1",ROOT.kOrange))
    sigSamples4.append(zprep.sample("data/MergedEleMva_20UL18_H2000A1.root","X2000Y1",ROOT.kOrange))

elif args.angle=="" and args.et=="":
    # if args.opt=="False" and args.era=="20UL18":
    #     sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_BuJpsiKee.root","Jpsi->ee",ROOT.kGray))
    sigSamples1 = addSigMC("20UL16APV")
    sigSamples2 = addSigMC("20UL16")
    sigSamples3 = addSigMC("20UL17")
    sigSamples4 = addSigMC("20UL18")

else:
    raise NameError('check dr/Et argument [""/None][Et1/Et2]')

workflowname = args.angle+args.et+'_'+args.det+'_ULall'
dfProducer = zprep.DataframeInitializer(args.det,args.angle,args.et,etThres)

def addBkgList(era):
    bkglist = [
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-0To70.root",53870.0),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-70To100.root",1283.0),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-100To200.root",1244.0),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-200To400.root",337.8),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-400To600.root",44.93),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-600To800.root",11.19),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-800To1200.root",4.926),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-1200To2500.root",1.152),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_WJets_HT-2500ToInf.root",0.02646),

        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-0To70.root",5379.0),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-70To100.root",140.0),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-100To200.root",139.2),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-200To400.root",38.4),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-400To600.root",5.174),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-600To800.root",1.258),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-800To1200.root",0.5598),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-1200To2500.root",0.1305),
        zprep.SampleProcessor("data/MergedEleMva_"+era+"_DY_HT-2500ToInf.root",0.002997),

        zprep.SampleProcessor("data/MergedEleMva_"+era+"_TT.root",471.7)
    ]

    return bkglist

bkglist1 = addBkgList("20UL16APV")
bkglist2 = addBkgList("20UL16")
bkglist3 = addBkgList("20UL17")
bkglist4 = addBkgList("20UL18")

col_names = dfProducer.col_names()

sum_bkg = 0.
sum_sig = 0.
n_sig = 0.

lumis = [19.5,16.8,41.48,59.83]

for i, aprocs in enumerate([bkglist1,bkglist2,bkglist3,bkglist4]):
    alumi = lumis[i]

    for aproc in aprocs:
        aproc.read(dfProducer)
        aproc.wgts_ *= alumi

for i, asamples in enumerate([sigSamples1,sigSamples2,sigSamples3,sigSamples4]):
    alumi = lumis[i]

    for asample in asamples:
        asample.read(dfProducer)
        asample.wgts_ *= alumi
        n_sig += np.sum(asample.wgts_)

for asample in [*sigSamples1,*sigSamples2,*sigSamples3,*sigSamples4]:
    asample.wgts_ *= asample.factor_*n_sig / np.sum(asample.wgts_)
    sum_sig += asample.factor_*n_sig

for aproc in [*bkglist1,*bkglist2,*bkglist3,*bkglist4]:
    sum_bkg += np.sum(aproc.wgts_)

for aproc in [*bkglist1,*bkglist2,*bkglist3,*bkglist4]:
    aproc.wgts_ *= n_sig/sum_bkg

for asample in [*sigSamples1,*sigSamples2,*sigSamples3,*sigSamples4]:
    asample.wgts_ *= n_sig/sum_sig

def retrieveSig(era):
    sigSamples = []

    if era=="20UL16APV":
        sigSamples = sigSamples1
    elif era=="20UL16":
        sigSamples = sigSamples2
    elif era=="20UL17":
        sigSamples = sigSamples2
    elif era=="20UL18":
        sigSamples = sigSamples2

    df_mergedEl = pd.concat([ asample.df_ for asample in sigSamples ], axis=0, ignore_index=True)
    wgts_mergedEl = np.concatenate([ asample.wgts_ for asample in sigSamples ], axis=0)
    pts_mergedEl = np.concatenate([ asample.pts_ for asample in sigSamples ], axis=0)
    etas_mergedEl = np.concatenate([ asample.etas_ for asample in sigSamples ], axis=0)
    drs_mergedEl = np.concatenate([ asample.drs_ for asample in sigSamples ], axis=0)

    return df_mergedEl, wgts_mergedEl, pts_mergedEl, etas_mergedEl, drs_mergedEl

df_mergedEl1, wgts_mergedEl1, pts_mergedEl1, etas_mergedEl1, drs_mergedEl1 = retrieveSig("20UL16APV")
df_mergedEl2, wgts_mergedEl2, pts_mergedEl2, etas_mergedEl2, drs_mergedEl2 = retrieveSig("20UL16")
df_mergedEl3, wgts_mergedEl3, pts_mergedEl3, etas_mergedEl3, drs_mergedEl3 = retrieveSig("20UL17")
df_mergedEl4, wgts_mergedEl4, pts_mergedEl4, etas_mergedEl4, drs_mergedEl4 = retrieveSig("20UL18")

def retrieveBkg(era):
    bkglist = []

    if era=="20UL16APV":
        bkglist = bkglist1
    elif era=="20UL16":
        bkglist = bkglist2
    elif era=="20UL17":
        bkglist = bkglist3
    elif era=="20UL18":
        bkglist = bkglist4

    # concat bkg
    df_bkg = pd.concat([ aproc.df_ for aproc in bkglist ], axis=0, ignore_index=True)
    wgts_bkg = np.concatenate([ aproc.wgts_ for aproc in bkglist ], axis=0)
    pts_bkg = np.concatenate([ aproc.pts_ for aproc in bkglist ], axis=0)
    etas_bkg = np.concatenate([ aproc.etas_ for aproc in bkglist ], axis=0)
    drs_bkg = np.concatenate([ aproc.drs_ for aproc in bkglist ], axis=0)

    return df_bkg, wgts_bkg, pts_bkg, etas_bkg, drs_bkg

df_bkg1, wgts_bkg1, pts_bkg1, etas_bkg1, drs_bkg1 = retrieveBkg("20UL16APV")
df_bkg2, wgts_bkg2, pts_bkg2, etas_bkg2, drs_bkg2 = retrieveBkg("20UL16")
df_bkg3, wgts_bkg3, pts_bkg3, etas_bkg3, drs_bkg3 = retrieveBkg("20UL17")
df_bkg4, wgts_bkg4, pts_bkg4, etas_bkg4, drs_bkg4 = retrieveBkg("20UL18")

transformer1 = sklearn.preprocessing.StandardScaler()
transformer2 = sklearn.preprocessing.StandardScaler()
transformer3 = sklearn.preprocessing.StandardScaler()
transformer4 = sklearn.preprocessing.StandardScaler()

plotname = workflowname

param = {'max_depth':4, 'objective':'binary:logistic', 'subsample':0.5, 'eval_metric':'logloss', 'tree_method':'exact'}

nbins = 100

bst1 = xgb.Booster(param)
bst2 = xgb.Booster(param)
bst3 = xgb.Booster(param)
bst4 = xgb.Booster(param)

npz_params1 = np.array([])
npz_params2 = np.array([])
npz_params3 = np.array([])
npz_params4 = np.array([])

targetThres = []

if args.angle=="None":
    bst1.load_model('model/NoneEt2_EB_20UL16APV.model')
    bst2.load_model('model/NoneEt2_EB_20UL16.model')
    bst3.load_model('model/NoneEt2_EB_20UL17.model')
    bst4.load_model('model/NoneEt2_EB_20UL18.model')
    npz_params1 = np.load('npz/NoneEt2_EB_20UL16APV.npz',allow_pickle=True)
    npz_params2 = np.load('npz/NoneEt2_EB_20UL16.npz',allow_pickle=True)
    npz_params3 = np.load('npz/NoneEt2_EB_20UL17.npz',allow_pickle=True)
    npz_params4 = np.load('npz/NoneEt2_EB_20UL18.npz',allow_pickle=True)
    targetThres = [0.674,0.667,0.632,0.625]
else:
    bst1.load_model('model/_EB_20UL16APV.model')
    bst2.load_model('model/_EB_20UL16.model')
    bst3.load_model('model/_EB_20UL17.model')
    bst4.load_model('model/_EB_20UL18.model')
    npz_params1 = np.load('npz/_EB_20UL16APV.npz',allow_pickle=True)
    npz_params2 = np.load('npz/_EB_20UL16.npz',allow_pickle=True)
    npz_params3 = np.load('npz/_EB_20UL17.npz',allow_pickle=True)
    npz_params4 = np.load('npz/_EB_20UL18.npz',allow_pickle=True)
    targetThres = [0.583,0.606,0.580,0.595]

# calculate scores by physics processes
def sig_predict(abst,atransformer,adf,awgt,colname):
    if adf.shape[0]==0:
        return np.zeros(shape=(adf.shape[0],))

    atrans= atransformer.transform(adf)
    admat = xgb.DMatrix(atrans, weight=awgt, label=np.ones(shape=(adf.shape[0],)), feature_names=colname)

    return abst.predict(admat)

def bkg_predict(abst,atransformer,adf,awgt,colname):
    if adf.shape[0]==0:
        return np.zeros(shape=(adf.shape[0],))

    atrans= atransformer.transform(adf)
    admat = xgb.DMatrix(atrans, weight=awgt, label=np.zeros(shape=(adf.shape[0],)), feature_names=colname)

    return abst.predict(admat)

np_meanstd1 = npz_params1['meanstd'][()]
np_meanstd2 = npz_params2['meanstd'][()]
np_meanstd3 = npz_params3['meanstd'][()]
np_meanstd4 = npz_params4['meanstd'][()]
transformer1.mean_ = np_meanstd1[0]
transformer1.scale_ = np_meanstd1[1]
transformer2.mean_ = np_meanstd2[0]
transformer2.scale_ = np_meanstd2[1]
transformer3.mean_ = np_meanstd3[0]
transformer3.scale_ = np_meanstd3[1]
transformer4.mean_ = np_meanstd4[0]
transformer4.scale_ = np_meanstd4[1]

score_list1 = []
score_list2 = []
score_list3 = []
score_list4 = []

for aproc in bkglist1:
    score_list1.append( bkg_predict(bst1,transformer1,aproc.df_,aproc.wgts_,col_names) )

for aproc in bkglist2:
    score_list2.append( bkg_predict(bst2,transformer2,aproc.df_,aproc.wgts_,col_names) )

for aproc in bkglist3:
    score_list3.append( bkg_predict(bst3,transformer3,aproc.df_,aproc.wgts_,col_names) )

for aproc in bkglist4:
    score_list4.append( bkg_predict(bst4,transformer4,aproc.df_,aproc.wgts_,col_names) )

scores_bkg1 = np.concatenate(score_list1, axis=0)
scores_bkg2 = np.concatenate(score_list2, axis=0)
scores_bkg3 = np.concatenate(score_list3, axis=0)
scores_bkg4 = np.concatenate(score_list4, axis=0)

ptBinning = [0,20,30,50,75,100,125,150,200,250,300,350,400,500,600,800,1000,1500]
effplot_bkg = ROOT.TEfficiency("eff_bkg",";E_{T}^{5x5};Efficiency",len(ptBinning)-1,array('d',ptBinning))

ptBinning750 = [0,20,50,100,150,200,220,240,260,280,300,320,340,360,380,400,450,500,600,800,1000,1500]
ptBinning2000 = [0,200,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000,1050,1100,1200,1300,1500]

drBinning = [0.,0.001,0.002,0.003,0.005,0.007,0.01,0.02,0.03,0.05,0.07,0.1,0.2,0.3,0.5,0.7,1.0]
effplot_dr_bkg = ROOT.TEfficiency("eff_dr_bkg",";#Delta R;Efficiency",len(drBinning)-1,array('d',drBinning))

effplot_sigs = []
effplot_dr_sigs = []
hist_dr_sigs = []

effplot_dr_bkg1 = ROOT.TEfficiency("eff_dr_bkg1",";#Delta R;Efficiency",len(drBinning)-1,array('d',drBinning))
effplot_dr_bkg2 = ROOT.TEfficiency("eff_dr_bkg2",";#Delta R;Efficiency",len(drBinning)-1,array('d',drBinning))
effplot_dr_bkg3 = ROOT.TEfficiency("eff_dr_bkg3",";#Delta R;Efficiency",len(drBinning)-1,array('d',drBinning))

effplot_dr_bkgs = [effplot_dr_bkg1,effplot_dr_bkg2,effplot_dr_bkg3]

for asample in sigSamples1:
    if "750" in asample.name_:
        effplot_sigs.append( ROOT.TEfficiency("eff_sig"+asample.name_,";E_{T}^{5x5};Efficiency",len(ptBinning750)-1,array('d',ptBinning750)) )
    elif "2000" in asample.name_:
        effplot_sigs.append( ROOT.TEfficiency("eff_sig"+asample.name_,";E_{T}^{5x5};Efficiency",len(ptBinning2000)-1,array('d',ptBinning2000)) )
    else:
        effplot_sigs.append( ROOT.TEfficiency("eff_sig"+asample.name_,";E_{T}^{5x5};Efficiency",len(ptBinning)-1,array('d',ptBinning)) )

    effplot_dr_sigs.append( ROOT.TEfficiency("eff_dr_sig"+asample.name_,";#Delta R;Efficiency",len(drBinning)-1,array('d',drBinning)) )
    hist_dr_sigs.append( ROOT.TH1D("hist_"+asample.name_,";#Delta R;NEvt",len(drBinning)-1,array('d',drBinning)) )

scores_bkg_all = [scores_bkg1,scores_bkg2,scores_bkg3,scores_bkg4]
wgts_bkg_all = [wgts_bkg1,wgts_bkg2,wgts_bkg3,wgts_bkg4]
pts_bkg_all = [pts_bkg1,pts_bkg2,pts_bkg3,pts_bkg4]
drs_bkg_all = [drs_bkg1,drs_bkg2,drs_bkg3,drs_bkg4]
transformer_all = [transformer1,transformer2,transformer3,transformer4]
sigSamples_all = [sigSamples1,sigSamples2,sigSamples3,sigSamples4]
bst_all = [bst1,bst2,bst3,bst4]

for i, target in enumerate(targetThres):
    scores_bkg = scores_bkg_all[i]
    wgts_bkg = wgts_bkg_all[i]
    pts_bkg = pts_bkg_all[i]
    drs_bkg = drs_bkg_all[i]

    for idx in range(len(wgts_bkg)):
        effplot_bkg.FillWeighted(scores_bkg[idx] > target, wgts_bkg[idx], pts_bkg[idx])
        effplot_dr_bkg.FillWeighted(scores_bkg[idx] > target, wgts_bkg[idx], drs_bkg[idx])

    sigSamples = sigSamples_all[i]
    transformer = transformer_all[i]
    bst = bst_all[i]

    for isample, asample in enumerate(sigSamples):
        for iEvt in range(len(asample.wgts_)):
            hist_dr_sigs[isample].Fill(asample.drs_[iEvt],asample.wgts_[iEvt])

    for isample, asample in enumerate(bkglist1):
        y_asample = np.zeros(shape=(asample.df_.shape[0],))
        trans_asample = transformer.transform(asample.df_)
        predict_asample = bst.predict( xgb.DMatrix(trans_asample, weight=asample.wgts_, label=y_asample, feature_names=col_names) )

        effIdx = -1

        if isample < 9:
            effIdx=0
        elif isample < 18:
            effIdx=1
        else:
            effIdx=2

        for iEvt in range(len(asample.wgts_)):
            effplot_dr_bkgs[effIdx].FillWeighted(predict_asample[iEvt] > target, asample.wgts_[iEvt], asample.drs_[iEvt])

for i, target in enumerate(targetThres):
    sigSamples = sigSamples_all[i]
    transformer = transformer_all[i]
    bst = bst_all[i]

    for isample, asample in enumerate(sigSamples):
        y_asample = np.ones(shape=(asample.df_.shape[0],))
        trans_asample = transformer.transform(asample.df_)
        predict_asample = bst.predict( xgb.DMatrix(trans_asample, weight=asample.wgts_, label=y_asample, feature_names=col_names) )
        hist_dr = hist_dr_sigs[isample]
        tot = hist_dr.Integral()

        for iEvt in range(len(asample.wgts_)):
            effplot_sigs[isample].FillWeighted(predict_asample[iEvt] > target, asample.wgts_[iEvt], asample.pts_[iEvt])

            if args.angle!="None" and hist_dr.GetBinContent( hist_dr.FindFixBin( asample.drs_[iEvt] ) )/tot > 0.005:
                effplot_dr_sigs[isample].FillWeighted(predict_asample[iEvt] > target, asample.wgts_[iEvt], asample.drs_[iEvt])

# some serious plotting
import CMS_lumi, tdrstyle

#set the tdr style
tdrstyle.setTDRStyle()

#change the CMS_lumi variables (see CMS_lumi.py)
CMS_lumi.writeExtraText = 1
CMS_lumi.extraText = "#splitline{       Simulation}{       Preliminary}"

CMS_lumi.lumi_sqrtS = "13 TeV"

iPos = 11
CMS_lumi.relPosX = 0.11

if( iPos==0 ):
    CMS_lumi.relPosX = 0.12

H_ref = 600;
W_ref = 600;
W = W_ref
H = H_ref

iPeriod = 0

# references for T, B, L, R
T = 0.08*H_ref
B = 0.12*H_ref
L = 0.12*W_ref
R = 0.04*W_ref

canvas = ROOT.TCanvas("c2","c2",50,50,W,H)
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

effplot_bkg.SetLineWidth(2)
effplot_bkg.SetLineColor(ROOT.kRed)
effplot_bkg.Draw()
canvas.Update()
agraph = effplot_bkg.GetPaintedGraph()
agraph.GetYaxis().SetTitleOffset(1)
agraph.GetXaxis().SetTitleSize(0.05)
agraph.GetYaxis().SetTitleSize(0.05)
agraph.GetXaxis().SetLabelSize(0.03)
agraph.GetYaxis().SetLabelSize(0.03)
agraph.GetHistogram().GetXaxis().SetLimits(0.,1500.)
agraph.SetMinimum(0.);
agraph.SetMaximum(1.4);
canvas.Update()

for idx, plot in enumerate(effplot_sigs):
    plot.SetLineWidth(2)
    plot.SetLineColor(sigSamples1[idx].color_)
    plot.Draw("sames")

# legend = ROOT.TLegend(0.5,0.75,0.95,0.9)
legend = ROOT.TLegend(0.5,0.82,0.95,0.9)
legend.SetBorderSize(0);
legend.SetNColumns(3)

for idx, plot in enumerate(effplot_sigs):
    legend.AddEntry(plot,sigSamples1[idx].name_)

legend.AddEntry(effplot_bkg,"Bkg")
legend.Draw()

#draw the lumi text on the canvas
CMS_lumi.CMS_lumi(canvas, iPeriod, iPos)
canvas.cd()
canvas.Update()
canvas.RedrawAxis()
frame = canvas.GetFrame()
frame.Draw()

canvas.SaveAs("plot/"+plotname+"_eff.pdf")

if args.angle!="None":
    canvas.SetLogx()
    effplot_dr_bkg.SetLineWidth(2)
    effplot_dr_bkg.SetLineColor(ROOT.kRed)
    effplot_dr_bkg.Draw()
    canvas.Update()
    agraph = effplot_dr_bkg.GetPaintedGraph()
    agraph.GetYaxis().SetTitleOffset(1)
    agraph.SetMinimum(0.);
    agraph.SetMaximum(1.4);
    canvas.Update()

    for idx, plot in enumerate(effplot_dr_sigs):
        plot.SetLineWidth(2)
        plot.SetLineColor(sigSamples[idx].color_)
        plot.Draw("sames")

    legend = ROOT.TLegend(0.5,0.75,0.95,0.9)
    legend.SetBorderSize(0);
    legend.SetNColumns(2)

    for idx, plot in enumerate(effplot_dr_sigs):
        legend.AddEntry(plot,sigSamples1[idx].name_)

    legend.AddEntry(effplot_dr_bkg,"bkg")
    legend.Draw()

    #draw the lumi text on the canvas
    CMS_lumi.CMS_lumi(canvas, iPeriod, iPos)
    canvas.cd()
    canvas.Update()
    canvas.RedrawAxis()
    frame = canvas.GetFrame()
    frame.Draw()

    canvas.SaveAs("plot/"+plotname+"_dr_eff.pdf")

    effplot_dr_bkgs[0].SetLineWidth(2)
    effplot_dr_bkgs[1].SetLineWidth(2)
    effplot_dr_bkgs[2].SetLineWidth(2)

    effplot_dr_bkgs[0].SetLineColor(ROOT.kRed-9)
    effplot_dr_bkgs[1].SetLineColor(ROOT.kOrange+1)
    effplot_dr_bkgs[2].SetLineColor(ROOT.kRed)

    effplot_dr_bkgs[0].Draw()
    canvas.Update()
    agraph = effplot_dr_bkgs[0].GetPaintedGraph()
    agraph.GetYaxis().SetTitleOffset(1)
    agraph.SetMinimum(0.);
    agraph.SetMaximum(1.4);
    canvas.Update()
    effplot_dr_bkgs[1].Draw("sames")
    effplot_dr_bkgs[2].Draw("sames")

    for idx, plot in enumerate(effplot_dr_sigs):
        plot.SetLineWidth(2)
        plot.SetLineColor(sigSamples[idx].color_)
        plot.Draw("sames")

    legend = ROOT.TLegend(0.5,0.75,0.95,0.9)
    legend.SetBorderSize(0);
    legend.SetNColumns(2)

    for idx, plot in enumerate(effplot_dr_sigs):
        legend.AddEntry(plot,sigSamples1[idx].name_)

    legend.AddEntry(effplot_dr_bkgs[0],"W")
    legend.AddEntry(effplot_dr_bkgs[1],"DY")
    legend.AddEntry(effplot_dr_bkgs[2],"TT")
    legend.Draw()

    #draw the lumi text on the canvas
    CMS_lumi.CMS_lumi(canvas, iPeriod, iPos)
    canvas.cd()
    canvas.Update()
    canvas.RedrawAxis()
    frame = canvas.GetFrame()
    frame.Draw()

    canvas.SaveAs("plot/"+plotname+"_dr_eff_separated.pdf")
