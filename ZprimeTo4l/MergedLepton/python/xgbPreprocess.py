import ROOT
import numpy as np
import pandas as pd
import math

def deltaPhi(phi1, phi2):
    dphi = phi2 - phi1
    if dphi > math.pi:
        dphi -= 2.*math.pi
    elif dphi <= -math.pi:
        dphi += 2.*math.pi

    return dphi

def reduceRange(x):
  o2pi = 1. / (2. * math.pi);
  if abs(x) <= math.pi:
    return x
  n = round(x * o2pi)
  return x - n * 2. * math.pi

def deltaR2(eta1,phi1,eta2,phi2):
    return abs(eta1-eta2)**2 + abs(deltaPhi(phi1,phi2))**2

class DataframeInitializer(object):
    """docstring for DataframeInitializer."""
    def __init__(self, det, ang, etrange, etThres):
        super(DataframeInitializer, self).__init__()
        self.det_ = det
        self.ang_ = ang
        self.et_ = etrange
        self.etThres_ = etThres
        self.col_ = []

        if ang=="None":
            self.col_.append(r'$\sigma_{i\eta i\eta}$')
            self.col_.append('E1x5/E5x5')
            self.col_.append(r'$\Delta\eta_{in}(seed)$')
            self.col_.append(r'$\Delta\phi_{in}(SC)$')
            self.col_.append('E/p')
        else:
            self.col_.append(r'$\alpha(union5x5)$')
            self.col_.append(r'$cov_{i\eta i\eta}(union5x5)$')
            self.col_.append(r'$\Delta\eta_{in}(union5x5)$')
            self.col_.append(r'$\Delta\phi_{in}(union5x5)$')
            self.col_.append(r'$\alpha(track)$')
            self.col_.append(r'$\Delta v_{in}/\Delta R_{trk}$')

    def col_names(self):
        return self.col_

    def fill_arr(self,aTree,aTrkTree=None):
        anArr = np.zeros(shape=(aTree.GetEntries(),len(self.col_)))
        wgts = np.zeros(shape=(aTree.GetEntries(),))
        pts = np.zeros(shape=(aTree.GetEntries(),))
        etas = np.zeros(shape=(aTree.GetEntries(),))
        drs = np.zeros(shape=(aTree.GetEntries(),))

        for iEl, el in enumerate(aTree):
            if self.det_=='EB':
                if abs(el.etaSC) > 1.4442:
                    continue
            elif self.det_=='EE':
                if abs(el.etaSC) < 1.566:
                    continue
            else:
                raise NameError('Please check EB/EE argument, the current argument is %s' % self.det_)

            if aTrkTree is not None:
                aTrkTree.GetEntry(iEl)

            eta1stGSF = -(el.dEtaSeed - el.etaSeed)
            u5x5Eta = el.union5x5dEtaIn + eta1stGSF
            u5x5Et = el.union5x5Energy/math.cosh(u5x5Eta)

            if self.et_=='Et1':
                if not ( u5x5Et > self.etThres_ and u5x5Et < 200. ):
                    continue
            elif self.et_=='Et2':
                if not ( u5x5Et >= self.etThres_ ):
                    continue
            elif self.et_=="":
                if not ( u5x5Et >= self.etThres_ ):
                    continue
            else:
                raise NameError('check Et argument (Et1/Et2)')

            if self.ang_=="None" and el.GsfPtErr/el.Gsfpt > 0.5:
                continue

            if el.GenPt > 0.:
                ratioU5x5 = u5x5Et / el.GenPt
                ratioSC = el.etSC / el.GenPt

                if ratioU5x5 < 0.8 or ratioU5x5 > 1.2:
                    continue

            idx = iEl
            wgts[idx] = el.weight/abs(el.weight)
            pts[idx] = u5x5Et
            etas[idx] = el.etaSC
            drs[idx] = -1.

            if self.ang_=="None":
                anArr[idx,0] = el.full5x5_sigmaIetaIeta
                anArr[idx,1] = el.full5x5_E1x5/el.full5x5_E5x5
                anArr[idx,2] = el.dEtaSeed
                anArr[idx,3] = el.dPhiIn
                anArr[idx,4] = el.EOverP
            else:
                anArr[idx,0] = el.alphaCalo
                anArr[idx,1] = el.union5x5covIeIe
                anArr[idx,2] = el.union5x5dEtaIn
                anArr[idx,3] = el.union5x5dPhiIn
                anArr[idx,4] = aTrkTree.alphaTrack
                anArr[idx,5] = aTrkTree.normalizedDParaIn

                drs[idx] = math.sqrt( deltaR2( aTrkTree.eta,aTrkTree.phi,el.Gsfeta,el.Gsfphi ) )

        # remove rows with only zeros
        mask = ~np.all(anArr==0.0,axis=1)
        anArr = anArr[mask]
        wgts = wgts[mask]
        pts = pts[mask]
        etas = etas[mask]
        drs = drs[mask]

        # remove rows with crazy values
        mask = ~np.any(np.abs(anArr)>10e+10,axis=1)
        anArr = anArr[mask]
        wgts = wgts[mask]
        pts = pts[mask]
        etas = etas[mask]
        drs = drs[mask]

        # sanity check
        if anArr.shape[0] != wgts.shape[0]:
            raise IndexError("Index of the array and the weight does not match!")

        aDf = pd.DataFrame(anArr,columns=self.col_)

        return aDf, wgts, pts, etas, drs

class SampleProcessor(object):
    """docstring for SampleProcessor."""
    def __init__(self, filename, xsec):
        super(SampleProcessor, self).__init__()
        self.filename_ = filename
        self.xsec_ = xsec
        self.df_ = None   # dataframe that contains ID variables
        self.wgts_ = None # np array of wgts for each electron
        self.pts_ = None   # np array of Et of each electron
        self.etas_ = None
        self.drs_ = None

    def read(self,dfProducer):
        afile = ROOT.TFile.Open(self.filename_)
        atree = None
        aTrkTree = None

        if dfProducer.ang_=="None":
            atree = afile.Get("mergedEleBkgMvaInput/bkg_elTree")
        else:
            atree = afile.Get("mergedEleBkgMvaInput/fake_elTree")
            aTrkTree = afile.Get("mergedEleBkgMvaInput/fakeTrk_addTrkTree")

        aWgtHist = afile.Get("mergedEleBkgMvaInput/totWeightedSum")
        totWgtSum = aWgtHist.GetBinContent(1)

        df, wgts, pts, etas, drs = dfProducer.fill_arr(atree,aTrkTree)
        wgts = wgts*(self.xsec_*1000./totWgtSum)

        self.df_ = df
        self.wgts_ = wgts
        self.pts_ = pts
        self.etas_ = etas
        self.drs_ = drs

        return

class sample(object):
    """docstring for sample."""
    def __init__(self, filename, samplename, acolor, factor=1.):
        super(sample, self).__init__()
        self.filename_ = filename
        self.df_ = None
        self.wgts_ = None
        self.pts_ = None
        self.etas_ = None
        self.drs_ = None
        self.name_ = samplename
        self.color_ = acolor
        self.factor_ = factor

    def read(self,dfProducer):
        afile = ROOT.TFile.Open(self.filename_)
        atree = None
        aTrkTree = None

        if dfProducer.ang_=="None":
            atree = afile.Get("mergedEleSigMvaInput/mergedEl2_elTree")
        else:
            atree = afile.Get("mergedEleSigMvaInput/mergedEl1_elTree")
            aTrkTree = afile.Get("mergedEleSigMvaInput/mergedEl1Trk_addTrkTree")

        aWgtHist = afile.Get("mergedEleSigMvaInput/totWeightedSum")
        totWgtSum = aWgtHist.GetBinContent(1)

        df, wgts, pts, etas, drs = dfProducer.fill_arr(atree,aTrkTree)
        wgts = wgts*(1000./totWgtSum)

        self.df_ = df
        self.wgts_ = wgts
        self.pts_ = pts
        self.etas_ = etas
        self.drs_ = drs

        return
