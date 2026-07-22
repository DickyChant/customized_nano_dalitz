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
parser.add_argument("--opt",dest="opt",type=str,help="perform training")
parser.add_argument("--era",dest="era",type=str,help="era (20UL16APV/20UL16/20UL17/20UL18)")
parser.add_argument("--model",dest="model",type=str,help="path to model",default="")
parser.add_argument("--cut",dest="cut",type=str,help="BDT score cut",default="")
parser.add_argument("--rwgt",dest="rwgt",type=str,help="do kinematic reweighting",default="False")

args = parser.parse_args()

# choose the right signal model for relevant phase spaces
sigSamples = []
etThres = 50.

if args.angle=="" and args.et=="Et1":
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H250A1.root","X250Y1",ROOT.kSpring+2))
elif args.angle=="" and args.et=="Et2":
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H750A1.root","X750Y1",ROOT.kTeal+2))
    etThres = 200.
elif args.angle=="None" and args.et=="Et2":
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H750A1.root","X750Y1",ROOT.kTeal+2))
    etThres = 200.

    if args.opt=="False":
        sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H2000A1.root","X2000Y1",ROOT.kOrange))

elif args.angle=="" and args.et=="":
    # if args.opt=="False" and args.era=="20UL18":
    #     sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_BuJpsiKee.root","Jpsi->ee",ROOT.kGray))

    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H2000A1.root","X2000Yiciency1",ROOT.kOrange))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H750A1.root","X750Yiciency1",ROOT.kSpring+2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H250A1.root","X250Yiciency1",ROOT.kTeal+2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H2000A10.root","X2000Yiciency10",ROOT.kCyan+2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H750A10.root","X750Yiciency10",ROOT.kAzure-2))
    sigSamples.append(zprep.sample("data/MergedEleMva_"+args.era+"_H250A10.root","X250Yiciency10",ROOT.kBlue+2))
else:
    raise NameError('check dr/Et argument [""/None][Et1/Et2]')

if args.opt=="False":
    etThres = 20.

workflowname = args.angle+args.et+'_'+args.det+'_'+args.era
dfProducer = zprep.DataframeInitializer(args.det,args.angle,args.et,etThres)

bkglist = [
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-0To70.root",53870.0),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-70To100.root",1283.0),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-100To200.root",1244.0),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-200To400.root",337.8),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-400To600.root",44.93),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-600To800.root",11.19),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-800To1200.root",4.926),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-1200To2500.root",1.152),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_WJets_HT-2500ToInf.root",0.02646),

    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-0To70.root",5379.0),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-70To100.root",140.0),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-100To200.root",139.2),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-200To400.root",38.4),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-400To600.root",5.174),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-600To800.root",1.258),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-800To1200.root",0.5598),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-1200To2500.root",0.1305),
    zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_DY_HT-2500ToInf.root",0.002997),

    # zprep.SampleProcessor("data/MergedEleMva_"+args.era+"_TT.root",471.7)
]

col_names = dfProducer.col_names()

sum_bkg = 0.
sum_sig = 0.
n_sig = 0.
n_bkg = 0.

for aproc in bkglist:
    aproc.read(dfProducer)

for asample in sigSamples:
    asample.read(dfProducer)
    n_sig += asample.wgts_.shape[0]

for asample in sigSamples:
    asample.wgts_ *= asample.factor_*n_sig / np.sum(asample.wgts_)
    sum_sig += asample.factor_*n_sig

df_mergedEl = pd.concat([ asample.df_ for asample in sigSamples ], axis=0, ignore_index=True)
wgts_mergedEl = np.concatenate([ asample.wgts_ for asample in sigSamples ], axis=0)
pts_mergedEl = np.concatenate([ asample.pts_ for asample in sigSamples ], axis=0)
etas_mergedEl = np.concatenate([ asample.etas_ for asample in sigSamples ], axis=0)
drs_mergedEl = np.concatenate([ asample.drs_ for asample in sigSamples ], axis=0)

# concat bkg
df_bkg = pd.concat([ aproc.df_ for aproc in bkglist ], axis=0, ignore_index=True)
wgts_bkg = np.concatenate([ aproc.wgts_ for aproc in bkglist ], axis=0)
pts_bkg = np.concatenate([ aproc.pts_ for aproc in bkglist ], axis=0)
etas_bkg = np.concatenate([ aproc.etas_ for aproc in bkglist ], axis=0)
drs_bkg = np.concatenate([ aproc.drs_ for aproc in bkglist ], axis=0)

if args.opt=="True" and args.rwgt=="True":
    # kinematic reweight for bkg
    ptBinning = [0,20,30,50,60,70,80,100,125,150,200,250,300,350,400,500,600,800,1000,1200,1500,2000]
    histEt = ROOT.TH1D("histPt",";E_{T};",len(ptBinning)-1,array('d',ptBinning))

    for pt, wgt in np.column_stack((pts_bkg,wgts_bkg)):
        histEt.Fill(pt,wgt)

    reweight = []

    for ibin in range(histEt.GetNbinsX()):
        wgt = 1./histEt.GetBinWidth(ibin+1)
        content = wgt*histEt.GetBinContent(ibin+1)

        if content==0.:
            reweight.append(1.)
        else:
            reweight.append(1./content)

    for aproc in bkglist:
        for idx in range(aproc.wgts_.shape[0]):
            ibin = histEt.FindFixBin(aproc.pts_[idx])

            if ibin <= histEt.GetNbinsX():
                aproc.wgts_[idx] *= reweight[ibin-1]

    del reweight, histEt

for aproc in bkglist:
    sum_bkg += np.sum(aproc.wgts_)
    n_bkg += aproc.wgts_.shape[0]

for aproc in bkglist:
    aproc.wgts_ *= n_sig/sum_bkg

for asample in sigSamples:
    asample.wgts_ *= n_sig/sum_sig

# replace wgts
wgts_mergedEl = np.concatenate([ asample.wgts_ for asample in sigSamples ], axis=0)
wgts_bkg = np.concatenate([ aproc.wgts_ for aproc in bkglist ], axis=0)

# prepare labels
y_mergedEl = np.ones(shape=(df_mergedEl.shape[0],))
y_bkgEl = np.zeros(shape=(df_bkg.shape[0],))

# concat sig+bkg
df_total = pd.concat([df_mergedEl,df_bkg], axis=0, ignore_index=True)
y_total = np.concatenate((y_mergedEl,y_bkgEl), axis=0)
wgts_total = np.concatenate((wgts_mergedEl,wgts_bkg), axis=0)

transformer = sklearn.preprocessing.StandardScaler()
x_total = transformer.fit_transform(df_total)
np_meanstd = np.array([transformer.mean_,transformer.scale_])

print('total number of merged objects = %d' % y_mergedEl.shape[0])
print('total number of bkg objects = %d' % y_bkgEl.shape[0])

dtotal = xgb.DMatrix(x_total, weight=wgts_total, label=y_total, feature_names=col_names)

# automatic hyper-optimization
def objective(params,dmat):
    param = {
        'max_depth': int(params['max_depth']),
        'eta': params['eta'],
        'gamma': params['gamma'],
        'lambda': params['lambda'],
        'min_child_weight':params['min_child_weight'],
        'objective':'binary:logistic',
        'subsample':0.5,
        'eval_metric':'logloss',
        'tree_method':'gpu_hist',
        'nthread':4
    }

    xgb_cv = xgb.cv(dtrain=dmat,nfold=5,num_boost_round=500,metrics='logloss',early_stopping_rounds=20,params=param)

    return xgb_cv['test-logloss-mean'].min()

if args.opt=="True": # hyper-optimization
    weightSum = np.sum(wgts_total)
    weightSumFrac = 1000.

    param_space = {
        'max_depth': hyperopt.hp.quniform('max_depth',1,4,1), # lower depth, more robust
        'eta': hyperopt.hp.loguniform('eta',-3.,-1.), # from exp(-3) to exp(-1)
        'gamma': hyperopt.hp.uniform('gamma',0.,10.),
        'lambda': hyperopt.hp.uniform('lambda',0.,2.),
        'min_child_weight': hyperopt.hp.loguniform('min_child_weight',math.log(weightSum/weightSumFrac),math.log(weightSum/10.))
    }

    trials = hyperopt.Trials()
    objec = lambda x: objective(x, dtotal)
    best = hyperopt.fmin(fn=objec, space=param_space, max_evals=256, algo=hyperopt.tpe.suggest, trials=trials)

    print('the best params are')
    print(best)

    # save hyper parameters
    np.savez('npz/'+workflowname+'.npz', meanstd=np_meanstd, bestparams=np.array(best))

# load hyper parameters
npz_params = np.array([])
plotname = workflowname

if args.model is not "" and os.path.splitext(args.model)[1]=='.model':
    npz_params = np.load('npz/'+os.path.splitext(os.path.basename(args.model))[0]+'.npz',allow_pickle=True)
    plotname += ('_'+os.path.splitext(os.path.basename(args.model))[0])
elif args.opt=="True":
    npz_params = np.load('npz/'+workflowname+'.npz',allow_pickle=True)
else:
    raise NameError('Neither loading existing model nor running the training, please check opt/model arguments')

param = npz_params['bestparams'][()] # numpy stores dict as 0-d array
param['max_depth'] = int(param['max_depth'])
param['objective'] = 'binary:logistic'
param['subsample'] = 0.5
param['eval_metric'] = 'logloss'
param['tree_method'] = 'exact'
param['nthread'] = 4

# run k-fold training, then pick the model with the smallest overtraining i.e. minimum |AUC(train)-AUC(test)|
kf = sklearn.model_selection.KFold(n_splits=5,shuffle=True)
modelPerforms_list = []
model_list = []

if args.opt=='True':
    for train, test in kf.split(x_total):
        x_train = x_total[train]
        y_train = y_total[train]
        wgts_train = wgts_total[train]

        x_test = x_total[test]
        y_test = y_total[test]
        wgts_test = wgts_total[test]

        dtrain = xgb.DMatrix(x_train, weight=wgts_train, label=y_train, feature_names=col_names)
        dtest = xgb.DMatrix(x_test, weight=wgts_test, label=y_test, feature_names=col_names)

        evallist = [(dtest, 'eval'), (dtrain, 'train')]
        num_round = 500

        bst = xgb.Booster(param)
        early_stop = xgb.callback.EarlyStopping(rounds=20,metric_name='logloss',data_name='eval')

        if args.opt=='True':
            bst = xgb.train(param, dtrain, num_round, evallist, callbacks=[early_stop])
            model_list.append(bst)

        dTrainPredict    = bst.predict(dtrain)
        dTestPredict     = bst.predict(dtest)

        modelPerforms_list.append( zvis.calROC(dTrainPredict,dTestPredict,y_train,y_test,wgts_train,wgts_test) )

targetFpr = 0.10
nbins = 100
idx_max = -1
targetThres = -1
trainThres = -1
bst = None

if args.opt=='True':
    # draw ROC curve and calculate score threshold
    idx_max = zvis.drawROC(modelPerforms_list, plotname+'_roc')
    targetThres, trainThres = zvis.drawThr(modelPerforms_list[idx_max], targetFpr, plotname+'_thr')

    # save model & importance plot
    bst = model_list[idx_max]
    bst.save_model('model/'+workflowname+'.model')
    gain = bst.get_score(importance_type='gain')
    cover = bst.get_score(importance_type='cover')
    zvis.drawImportance(gain,cover,col_names,plotname+'_importance')
else:
    bst = xgb.Booster(param)
    bst.load_model('model/'+os.path.splitext(os.path.basename(args.model))[0]+'.model')

# calculate scores by physics processes
def bkg_predict(abst,atransformer,adf,awgt,colname):
    if adf.shape[0]==0:
        return np.zeros(shape=(adf.shape[0],))

    atrans= atransformer.transform(adf)
    admat = xgb.DMatrix(atrans, weight=awgt, label=np.zeros(shape=(adf.shape[0],)), feature_names=colname)

    return abst.predict(admat)

np_meanstd = npz_params['meanstd'][()]
transformer.mean_ = np_meanstd[0]
transformer.scale_ = np_meanstd[1]
trans_mergedEl = transformer.transform(df_mergedEl)
dSig = xgb.DMatrix(trans_mergedEl, weight=wgts_mergedEl, label=y_mergedEl, feature_names=col_names)
dSigPredict = bst.predict(dSig)

score_list = []

for aproc in bkglist:
    score_list.append( bkg_predict(bst,transformer,aproc.df_,aproc.wgts_,col_names) )

scores_bkg = np.concatenate(score_list, axis=0)

if args.opt=="False" and args.cut=="":
    score_all = np.concatenate([dSigPredict,scores_bkg], axis=0)
    modelPerforms_list.append( zvis.calROC(score_all,score_all,y_total,y_total,wgts_total,wgts_total) )
    zvis.drawROC(modelPerforms_list, plotname+'_roc')
    targetThres, trainThres = zvis.drawThr(modelPerforms_list[idx_max], targetFpr, plotname+'_thr')
elif args.cut!="":
    targetThres = float(args.cut)

zvis.drawScoreByProcess(
    dSigPredict,
    wgts_mergedEl,
    list(np.array([aproc for aproc in reversed(score_list)],dtype=object)),
    list(np.array([aproc.wgts_ for aproc in reversed(bkglist)],dtype=object)),
    ['_','_','_','_','DY','_','_','_','_',
    '_','_','_','_','WJets','_','_','_','_'],
    ['wheat','wheat','wheat','wheat','wheat','wheat','wheat','wheat','wheat',
    'green','green','green','green','green','green','green','green','green'],
    nbins,
    plotname+'_scoreProcess'
)

zvis.drawScoreByProcess(
    None,
    None,
    # hail python
    list(np.array([aproc.etas_[score_list[idx] > targetThres] for idx, aproc in reversed(list(enumerate(bkglist)))],dtype=object)),
    list(np.array([aproc.wgts_[score_list[idx] > targetThres] for idx, aproc in reversed(list(enumerate(bkglist)))],dtype=object)),
    ['_','_','_','_','DY','_','_','_','_',
    '_','_','_','_','WJets','_','_','_','_'],
    ['wheat','wheat','wheat','wheat','wheat','wheat','wheat','wheat','wheat',
    'green','green','green','green','green','green','green','green','green'],
    100,
    plotname+'_etaSC'
)

ptBinning = [0,20,30,50,75,100,125,150,200,250,300,350,400,500,600,800,1000,1500]
effplot_bkg = ROOT.TEfficiency("eff_bkg",";E_{T}^{5x5};Efficiency",len(ptBinning)-1,array('d',ptBinning))

ptBinning750 = [0,20,50,100,150,200,220,240,260,280,300,320,340,360,380,400,450,500,600,800,1000,1500]
ptBinning2000 = [0,200,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000,1050,1100,1200,1300,1500]

etaBinning = [-2.5,-2.,-1.566,-1.4442,-1.2,-0.8,-0.4,0.,0.4,0.8,1.2,1.4442,1.566,2.,2.5]
effplot_etaSC_sig = ROOT.TEfficiency("eff_etaSC_sig",";#eta_{SC};Efficiency",len(etaBinning)-1,array('d',etaBinning))
effplot_etaSC_bkg = ROOT.TEfficiency("eff_etaSC_bkg",";#eta_{SC};Efficiency",len(etaBinning)-1,array('d',etaBinning))

drBinning = [0.,0.001,0.002,0.003,0.005,0.007,0.01,0.02,0.03,0.05,0.07,0.1,0.2,0.3,0.5,0.7,1.0]
effplot_dr_bkg = ROOT.TEfficiency("eff_dr_bkg",";#Delta R;Efficiency",len(drBinning)-1,array('d',drBinning))

effplot_sigs = []
effplot_dr_sigs = []

for asample in sigSamples:
    if "750" in asample.name_:
        effplot_sigs.append( ROOT.TEfficiency("eff_sig"+asample.name_,";E_{T}^{5x5};Efficiency",len(ptBinning750)-1,array('d',ptBinning750)) )
    elif "2000" in asample.name_:
        effplot_sigs.append( ROOT.TEfficiency("eff_sig"+asample.name_,";E_{T}^{5x5};Efficiency",len(ptBinning2000)-1,array('d',ptBinning2000)) )
    else:
        effplot_sigs.append( ROOT.TEfficiency("eff_sig"+asample.name_,";E_{T}^{5x5};Efficiency",len(ptBinning)-1,array('d',ptBinning)) )

    effplot_dr_sigs.append( ROOT.TEfficiency("eff_dr_sig"+asample.name_,";#Delta R;Efficiency",len(drBinning)-1,array('d',drBinning)) )

for idx in range(len(wgts_mergedEl)):
    effplot_etaSC_sig.FillWeighted(dSigPredict[idx] > targetThres, wgts_mergedEl[idx], etas_mergedEl[idx])

for idx in range(len(wgts_bkg)):
    effplot_bkg.FillWeighted(scores_bkg[idx] > targetThres, wgts_bkg[idx], pts_bkg[idx])
    effplot_etaSC_bkg.FillWeighted(scores_bkg[idx] > targetThres, wgts_bkg[idx], etas_bkg[idx])
    effplot_dr_bkg.FillWeighted(scores_bkg[idx] > targetThres, wgts_bkg[idx], drs_bkg[idx])

for idx, asample in enumerate(sigSamples):
    y_asample = np.ones(shape=(asample.df_.shape[0],))
    trans_asample = transformer.transform(asample.df_)
    predict_asample = bst.predict( xgb.DMatrix(trans_asample, weight=asample.wgts_, label=y_asample, feature_names=col_names) )

    for iEvt in range(len(asample.wgts_)):
        effplot_sigs[idx].FillWeighted(predict_asample[iEvt] > targetThres, asample.wgts_[iEvt], asample.pts_[iEvt])
        effplot_dr_sigs[idx].FillWeighted(predict_asample[iEvt] > targetThres, asample.wgts_[iEvt], asample.drs_[iEvt])

# some serious plotting
import CMS_lumi, tdrstyle

#set the tdr style
tdrstyle.setTDRStyle()

#change the CMS_lumi variables (see CMS_lumi.py)
CMS_lumi.writeExtraText = 1
CMS_lumi.extraText = "#splitline{       Simulation}{       Preliminary}"

if args.era=="20UL16APV":
    CMS_lumi.lumi_sqrtS = "2016preVFP"
elif args.era=="20UL16":
    CMS_lumi.lumi_sqrtS = "2016postVFP"
elif args.era=="20UL17":
    CMS_lumi.lumi_sqrtS = "2017"
elif args.era=="20UL18":
    CMS_lumi.lumi_sqrtS = "2018"

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
    plot.SetLineColor(sigSamples[idx].color_)
    plot.Draw("sames")

# legend = ROOT.TLegend(0.5,0.75,0.95,0.9)
legend = ROOT.TLegend(0.5,0.82,0.95,0.9)
legend.SetBorderSize(0);
legend.SetNColumns(3)

for idx, plot in enumerate(effplot_sigs):
    legend.AddEntry(plot,sigSamples[idx].name_)

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

effplot_etaSC_bkg.SetLineWidth(2)
effplot_etaSC_sig.SetLineWidth(2)
effplot_etaSC_bkg.SetLineColor(ROOT.kRed)
effplot_etaSC_sig.SetLineColor(ROOT.kBlue)
effplot_etaSC_bkg.Draw()
canvas.Update()
agraph = effplot_etaSC_bkg.GetPaintedGraph()
agraph.GetYaxis().SetTitleOffset(1)
agraph.SetMinimum(0.);
agraph.SetMaximum(1.2);
canvas.Update()
effplot_etaSC_sig.Draw("sames")

legend = ROOT.TLegend(0.85,0.8,0.98,0.9)
legend.SetBorderSize(0);
legend.AddEntry(effplot_etaSC_sig,"sig")
legend.AddEntry(effplot_etaSC_bkg,"bkg")
legend.Draw()

#draw the lumi text on the canvas
CMS_lumi.CMS_lumi(canvas, iPeriod, iPos)
canvas.cd()
canvas.Update()
canvas.RedrawAxis()
frame = canvas.GetFrame()
frame.Draw()

canvas.SaveAs("plot/"+plotname+"_etaSC_eff.png")

if args.angle!="None":
    canvas.SetLogx()
    effplot_dr_bkg.SetLineWidth(2)
    effplot_dr_bkg.SetLineColor(ROOT.kRed)
    effplot_dr_bkg.Draw()
    canvas.Update()
    agraph = effplot_dr_bkg.GetPaintedGraph()
    agraph.GetYaxis().SetTitleOffset(1)
    agraph.SetMinimum(0.);
    agraph.SetMaximum(1.2);
    canvas.Update()

    for idx, plot in enumerate(effplot_dr_sigs):
        plot.SetLineWidth(2)
        plot.SetLineColor(sigSamples[idx].color_)
        plot.Draw("sames")

    legend = ROOT.TLegend(0.15,0.75,0.38,0.9)
    legend.SetBorderSize(0);
    legend.SetNColumns(2)

    for idx, plot in enumerate(effplot_dr_sigs):
        legend.AddEntry(plot,sigSamples[idx].name_)

    legend.AddEntry(effplot_dr_bkg,"bkg")
    legend.Draw()

    #draw the lumi text on the canvas
    CMS_lumi.CMS_lumi(canvas, iPeriod, iPos)
    canvas.cd()
    canvas.Update()
    canvas.RedrawAxis()
    frame = canvas.GetFrame()
    frame.Draw()

    canvas.SaveAs("plot/"+plotname+"_dr_eff.png")
