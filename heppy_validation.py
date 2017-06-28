from __future__ import absolute_import

import logging
import os
import uuid

from rootpy import ROOT
from rootpy.io import root_open
from rootpy.plotting import Canvas, Hist, HistStack, Legend

from Xbb.utils import path

# Set ROOT to batch mode.
ROOT.gROOT.SetBatch(True)

LOGGER = logging.getLogger(__name__)


class HeppyValidationPlot(object):

    def __init__(self, version_old, version_new):
        self.version_old = version_old
        self.version_new = version_new
        self.dest = 'Validation{0}to{1}'.format(version_old, version_new)
        path.safe_makedirs(self.dest)

    def __call__(self, sample_old, sample_new, name, options):
        h_old = self.get_histogram(sample_old, title=self.version_old, **options)
        h_new = self.get_histogram(sample_new, title=self.version_new, **options)
        h_old.legendstyle = 'l'
        h_new.legendstyle= 'l'
        h_stack = self.make_stack(h_old, h_new)
        self.draw(h_stack, name, **options)
    
    def get_histogram(self, sample, title, varexp, binning, selection='', *args, **kwargs):
        name = 'h_{!s}'.format(uuid.uuid4().hex)
        expression = '{0}>>h_{1}({2})'.format(varexp, name, ','.join(value for value in binning))
        LOGGER.debug('Drawing %s with binning %s into histogram %s', varexp, binning, name)
        with root_open(sample) as f:
            t = f.Get('tree')
            h = t.Draw(expression, '', 'goff norm')
            h.SetTitle(title)
            return h

    def make_stack(self, h_old, h_new):
        h_old.SetLineColor('red')
        h_new.SetLineColor('blue')
        h_stack = HistStack(stacked=False)
        h_stack.Add(h_old)
        h_stack.Add(h_new)
        return h_stack

    def draw(self, h_stack, name, x_title, *args, **kwargs):
        canvas = Canvas()
        h_stack.Draw('hist nostack')
        h_stack.xaxis.SetTitle(x_title)
        h_stack.SetMaximum(h_stack.max() * 1.15)
        legend = Legend(h_stack.hists)
        legend.Draw()
        outfile = os.path.join(self.dest, name + '.png')
        canvas.SaveAs(outfile)


if __name__ == '__main__':

    logging.basicConfig(format='[%(name)s] %(levelname)s: %(message)s', level=logging.DEBUG)

    # Samples
    XRD_REDIRECTOR = 'root://cms-xrd-global.cern.ch//'
    #XRD_REDIRECTOR = 'root://xrootd-cms.infn.it//'
    SAMPLE_OLD = XRD_REDIRECTOR + '/store/user/perrozzi/VHBBHeppyV23/TT_TuneCUETP8M1_13TeV-powheg-pythia8/VHBB_HEPPY_V23_TT_TuneCUETP8M1_13TeV-powheg-Py8__spr16MAv2-puspr16_80r2as_2016_MAv2_v0_ext3-v2/160717_083929/0000/tree_1.root'
    SAMPLE_NEW = XRD_REDIRECTOR + '/store/user/arizzi/VHBBHeppyV24/TT_TuneCUETP8M1_13TeV-powheg-pythia8/VHBB_HEPPY_V24_TT_TuneCUETP8M1_13TeV-powheg-Py8__spr16MAv2-puspr16_HLT_80r2as_v14_ext3-v1/160909_063406/0000/tree_1.root'

    # MET2016B
    # /store/user/cvernier/VHBBHeppyV23/MET/VHBB_HEPPY_V23_MET__Run2016B-PromptReco-v2/160717_203439/0000/tree_10.root
    # /store/user/arizzi/VHBBHeppyV24/MET/VHBB_HEPPY_V24_MET__Run2016B-PromptReco-v2/160910_205551/0000/tree_10.root

    # QCDHT200
    # /store/user/perrozzi/VHBBHeppyV23/QCD_HT200to300_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V23_QCD_HT200to300_TuneCUETP8M1_13TeV-madgraphMLM-Py8__spr16MAv2-puspr16_80r2as_2016_MAv2_v0_ext1-v1/160717_082458/0000/tree_1.root
    # /store/user/arizzi/VHBBHeppyV24/QCD_HT200to300_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/VHBB_HEPPY_V24_QCD_HT200to300_TuneCUETP8M1_13TeV-madgraphMLM-Py8__spr16MAv2-puspr16_80r2as_2016_MAv2_v0_ext1-v1/160909_075702/0000/tree_1.root

    # ZJetsHT200
    # /store/user/perrozzi/VHBBHeppyV23/ZJetsToNuNu_HT-200To400_13TeV-madgraph/VHBB_HEPPY_V23_ZJetsToNuNu_HT-200To400_13TeV-madgraph__spr16MAv2-puspr16_80r2as_2016_MAv2_v0_ext1-v1/160718_081847/0000/tree_1.root
    # /store/user/arizzi/VHBBHeppyV24/ZJetsToNuNu_HT-200To400_13TeV-madgraph/VHBB_HEPPY_V24_ZJetsToNuNu_HT-200To400_13TeV-madgraph__spr16MAv2-puspr16_80r2as_2016_MAv2_v0_ext1-v1/160909_073933/0000/tree_1.root

    # TT
    # /store/user/perrozzi/VHBBHeppyV23/TT_TuneCUETP8M1_13TeV-powheg-pythia8/VHBB_HEPPY_V23_TT_TuneCUETP8M1_13TeV-powheg-Py8__spr16MAv2-puspr16_80r2as_2016_MAv2_v0_ext3-v2/160717_083929/0000/tree_1.root
    # /store/user/arizzi/VHBBHeppyV24/TT_TuneCUETP8M1_13TeV-powheg-pythia8/VHBB_HEPPY_V24_TT_TuneCUETP8M1_13TeV-powheg-Py8__spr16MAv2-puspr16_HLT_80r2as_v14_ext3-v1/160909_063406/0000/tree_1.root

    # Plots
    PLOTS = {
        'met_pt': {
            'varexp': 'met_pt',
            'binning': ['50', '0', '500'],
            'x_title': '#slash{E}_{T} [GeV]',
        },

        'HCSV_pt': {
            'varexp': 'HCSV_pt',
            'binning': ['20', '0', '400'],
            'x_title': 'p_{T}(HCSV) [GeV]',
        },

        'HCSV_reg_pt': {
            'varexp': 'HCSV_reg_pt',
            'binning': ['20', '0', '400'],
            'x_title': 'p_{T}^{reg}(HCSV) [GeV]',
        },

        'HCSV_mass': {
            'varexp': 'HCSV_mass',
            'binning': ['40', '0', '400'],
            'x_title': 'm_{jj}(HCSV) [GeV]',
        },

        'HCSV_reg_mass': {
            'varexp': 'HCSV_reg_mass',
            'binning': ['40', '0', '400'],
            'x_title': 'm_{jj}^{reg}(HCSV) [GeV]',
        },

        'hJet1_pt': {
            'varexp': 'Jet_pt[hJCidx[0]]',
            'binning': ['50', '0', '400'],
            'x_title': 'p_{T}(j1) [GeV]',
        },

        'hJet1_reg_pt': {
            'varexp': 'Jet_pt_reg[hJCidx[0]]',
            'binning': ['50', '0', '400'],
            'x_title': 'p_{T}^{reg}(j1) [GeV]',
        },

        'hJet2_pt': {
            'varexp': 'Jet_pt[hJCidx[1]]',
            'binning': ['50', '0', '400'],
            'x_title': 'p_{T}(j2) [GeV]',
        },

        'hJet2_reg_pt': {
            'varexp': 'Jet_pt_reg[hJCidx[1]]',
            'binning': ['50', '0', '400'],
            'x_title': 'p_{T}^{reg}(j2) [GeV]',
        },

        'hJet1_CSV': {
            'varexp': 'Jet_btagCSV[hJCidx[0]]',
            'binning': ['40', '0', '1'],
            'x_title': 'CSV_{max}',
        },

        'hJet2_CSV': {
            'varexp': 'Jet_btagCSV[hJCidx[1]]',
            'binning': ['40', '0', '1'],
            'x_title': 'CSV_{min}',
        },

    }

    plotter = HeppyValidationPlot('V23', 'V24')
    for plot, options in PLOTS.iteritems():
        plotter(SAMPLE_OLD, SAMPLE_NEW, plot, options)

