#!/usr/bin/env python
import logging
import sys

import ROOT
import numpy


# The path to the signal region shapes file.
SIGNAL_SHAPES_PATH = 'vhbb_TH_Znn_13TeV_Signal.root'
# The name of the signal region bin in the signal region shapes file.
SIGNAL_SHAPES_BIN = 'Znn_13TeV_Signal'
# The path to the mlfit.root file.
MLFIT_PATH = 'mlfit.root'
# The name of the signal region bin in the mlfit.root file.
MLFIT_BIN = 'Znn_SR'
# The name of the branch containing the nominal BDT score.
BDT_BRANCH = 'BDT_Znn_HighPt.Nominal'


def get_shape_bin_edges(shapes_path, datacard_bin):
    """Return an array of the bin edges used by the input shapes.

    Parameters
    ----------
    shapes_path : path
        The path to the shapes file.
    datacard_bin : string
        The name of the datacard bin containing the shapes.

    Returns
    -------
    bin_edges : numpy.array
        The array of bin edges.
    """
    shapes_file = ROOT.TFile.Open(shapes_path)
    shapes_file.cd(datacard_bin)
    shapes = ROOT.gDirectory.GetListOfKeys()
    # Since the nominal and varied shapes share the same binning,
    # take any of the histograms found in the shapes file.
    shape = ROOT.gDirectory.Get(shapes[0].GetName())
    bin_edges = numpy.array(
        [shape.GetXaxis().GetBinLowEdge(i) for i in xrange(1, shape.GetNbinsX() + 1)],
        dtype=numpy.float64,
    )
    shapes_file.Close()
    return bin_edges


def get_total_postfit_shapes(mlfit_path, datacard_bin, bin_edges):
    """Retrun the rebinned the postfit shapes for the total
    signal and total background from an mlfit.root file.

    Parameters
    ----------
    mlfit_path : path
        The path to the mlfit.root file.
    datacard_bin : string
        The name of the datacard bin containing the shapes.
    bin_edges : numpy.array of float
        An array of bin low edge values used to rebin the postfit shapes.

    Returns
    -------
    signal_postfit, background_postfit : tuple of ROOT.TH1F
        The rebinned signal and background postfit shapes.
    """
    mlfit_file = ROOT.TFile.Open(mlfit_path)
    mlfit_file.cd('shapes_fit_s/{}'.format(datacard_bin))
    total_signal = ROOT.gDirectory.Get('total_signal')
    total_background = ROOT.gDirectory.Get('total_background')
    total_signal.SetDirectory(0)
    total_background.SetDirectory(0)
    mlfit_file.Close()
    signal_postfit = ROOT.TH1F('signal_postfit', '', len(bin_edges) - 1, bin_edges)
    background_postfit = signal_postfit.Clone('background_postfit')
    for i in xrange(1, signal_postfit.GetNbinsX() + 1):
        signal_postfit.SetBinContent(i, total_signal.GetBinContent(i))
        background_postfit.SetBinContent(i, total_background.GetBinContent(i))
    return signal_postfit, background_postfit


def add_sb_weight(src, dst, bdt_branch, signal_postfit, background_postfit):
    """Add a branch named "sb_weight" which contains the per-event S/(S+B) weight
    for the events' corresponding bin in the signal region BDT score distribution.
    This is to be applied to all MC and data.

    Parameters
    ----------
    src : path
        The path to the input ntuple.
    dst : path
        The path to the output ntuple.
    bdt_branch : string
        The name of the branch containing the nominal BDT score.
    signal_postfit : ROOT.TH1F
        The postfit total signal shape.
    background_postfit : ROOT.TH1F
        The postfit total background shape.
    """
    logger = logging.getLogger('add_sb_weight')
    # Copy any count and weight histograms.
    infile = ROOT.TFile.Open(src)
    outfile = ROOT.TFile.Open(dst, 'recreate')
    for key in infile.GetListOfKeys():
        if key.GetName() == 'tree':
            continue
        obj = key.ReadObj()
        obj.Write()
    tree = infile.Get('tree')
    # Reset the branch in case it already exists.
    tree.SetBranchStatus('sb_weight', 0)
    # Set the BDT branch address for faster reading, making
    # sure that Xbb-style leaflists are handled properly.
    if '.' in bdt_branch:
        branch_name, leaf_name = bdt_branch.split('.')
        branch = tree.GetBranch(branch_name)
        n_leaves = branch.GetNleaves()
        leaf_index = [leaf.GetName() for leaf in branch.GetListOfLeaves()].index(leaf_name)
        bdt_buffer = numpy.zeros(n_leaves, dtype=numpy.float32)
    else:
        branch_name = bdt_branch
        leaf_index = None
        bdt_buffer = numpy.zeros(1, dtype=numpy.float32)
    tree.SetBranchAddress(branch_name, bdt_buffer)
    # Clone the original tree and add the new branch.
    tree_new = tree.CloneTree(0)
    sb_weight = numpy.zeros(1, dtype=numpy.float64)
    tree_new.Branch('sb_weight', sb_weight, 'sb_weight/D')
    # Cache the Fill method for faster filling.
    fill_tree_new = tree_new.Fill
    for i, event in enumerate(tree, start=1):
        # Find the BDT bin containing the event. If the event is
        # found in the underflow bin, use the first bin instead.
        bdt_score = bdt_buffer[0] if leaf_index is None else bdt_buffer[leaf_index]
        bin_index = signal_postfit.FindBin(bdt_score) or 1
        # Calculate the S/(S+B) weight for the event.
        s = signal_postfit.GetBinContent(bin_index)
        b = background_postfit.GetBinContent(bin_index)
        sb_weight[0] = s / (s + b) if b > 0 else 0
        fill_tree_new()
        if i % 1000 == 0 or sb_weight[0] > 10:
            logger.info('Processing Entry #%s: BDT Score = %s, S/(S+B) = %s', i, bdt_score, sb_weight)
    tree_new.Write()
    outfile.Close()
    infile.Close()


def main():
    """Example usage:
    python add_sb_weight.py ZH_HToBB_ZToNuNu_M125_13TeV_powheg_pythia8.root ZH_HToBB_ZToNuNu_M125_13TeV_powheg_pythia8_new.root
    """
    logging.basicConfig(format='[%(name)s] %(levelname)s - %(message)s', level=logging.INFO)
    bin_edges = get_shape_bin_edges(SIGNAL_SHAPES_PATH, SIGNAL_SHAPES_BIN)
    signal_postfit, background_postfit = get_total_postfit_shapes(MLFIT_PATH, MLFIT_BIN, bin_edges)
    add_sb_weight(sys.argv[1], sys.argv[2], BDT_BRANCH, signal_postfit, background_postfit)


if __name__ == '__main__':

    status = main()
    sys.exit(status)

