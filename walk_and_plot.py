import sys

import ROOT


def walk_and_plot(directory):
    """Recursively walk a TDirectory and plot all encountered histograms.

    Parameters
    ----------
    directory : ROOT.TDirectory
        The TFile or TDirectory to walk.
    """
    c = ROOT.TCanvas('c_{}'.format(directory.GetName()))
    for key in directory.GetListOfKeys():
        name = key.GetName()
        obj = key.ReadObj()
        if key.IsFolder():
            obj.cd()
            walk_and_plot(obj)
        if obj.InheritsFrom(ROOT.TH1.Class()):
            obj.Draw('colz')
            c.SaveAs('{}.png'.format(name))
    c.IsA().Destructor(c)


def main():
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    f = ROOT.TFile.Open(sys.argv[1])
    walk_and_plot(f)
    f.Close()


if __name__ == '__main__':

    status = main()
    sys.exit(status)

