import ROOT
import numpy


class PrefitFile(object):
    def __init__(self, path):
        self.path = path

    def get_shapes(self):
        """Get the prefit shapes.
        """
        f = ROOT.TFile.Open(self.path)
        if isinstance(f.GetListOfKeys()[0].ReadObj(), ROOT.TDirectory):
            f.cd(f.GetListOfKeys()[0].GetName())
        shapes = [key.ReadObj() for key in ROOT.gDirectory.GetListOfKeys() if 'cms' not in key.GetName().lower()]
        for shape in shapes:
            shape.SetDirectory(0)
        f.Close()
        return shapes


class MlfitFile(object):
    def __init__(self, path):
        self.path = path

    def get_shapes(self, folder, x_bins):
        """Get the postfit shapes inside a given folder,
        rebinning them according to x_bins.
        """
        f = ROOT.TFile.Open(self.path)
        f.cd(folder)
        shapes = [key.ReadObj() for key in ROOT.gDirectory.GetListOfKeys() if key.GetName() not in {'data', 'total_covar'}]
        shapes_rebinned = [self._rebin_shape(shape, x_bins) for shape in shapes]
        for shape in shapes_rebinned:
            shape.SetDirectory(0)
        f.Close()
        return shapes_rebinned

    def _rebin_shape(self, shape, x_bins):
        """Rebin the postfit shapes to match their prefit binning.
        """
        hrebin = ROOT.TH1F(shape.GetName(), '', len(x_bins) - 1, x_bins)
        for i in xrange(1, hrebin.GetNbinsX() + 1):
            hrebin.SetBinContent(i, shape.GetBinContent(i))
            hrebin.SetBinError(i, shape.GetBinError(i))
        return hrebin


def get_x_bins(histogram):
    """Return an array of bin low edges and the upper edge of the last bin for a histogram.
    """
    x_axis = histogram.GetXaxis()
    x_bins = [x_axis.GetBinLowEdge(i) for i in xrange(1, histogram.GetNbinsX() + 2)]
    return numpy.array(x_bins, dtype=numpy.float64)


def write_objects(objects, dst, directory):
    """Write an iterable collection of objects to a directory in a ROOT file.
    """
    dst.mkdir(directory)
    dst.cd(directory)
    for obj in objects:
        obj.Write()


if __name__ == '__main__':

    VH = {
        'name': 'VH',
        'prefit': {
            'Znn': PrefitFile('VH_combo_7_12/ZnnHbb_Datacards_Jun18_Minus0p8_to_Plus1_NoLowStatShapes/vhbb_TH_Znn_13TeV_Signal.root'),
            'Wen': PrefitFile('VH_combo_7_12/WlvHbb/hists_WenHighPt.root'),
            'Wmn': PrefitFile('VH_combo_7_12/WlvHbb/hists_WmnHighPt.root'),
            'ZeeLowPt': PrefitFile('VH_combo_7_12/ZllHbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zee_LowPt.root'),
            'ZmmLowPt': PrefitFile('VH_combo_7_12/ZllHbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zuu_LowPt.root'),
            'ZeeHighPt': PrefitFile('VH_combo_7_12/ZllHbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zee_HighPt.root'),
            'ZmmHighPt': PrefitFile('VH_combo_7_12/ZllHbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zuu_HighPt.root'),
        },
        'mlfit': MlfitFile('VH_combo_7_12/mlfit.root'),
    }

    VZ = {
        'name': 'VZ',
        'prefit': {
            'Znn': PrefitFile('VZcombo_7_3/ZnnZbb_Datacards_Jun19_Minus0p8_to_Plus1_NoLowStatShapes/vhbb_TH_Znn_13TeV_Signal.root'),
            'Wen': PrefitFile('VZcombo_7_3/WlnZbb_Datacards_April6_v2_BTFullDecorr_WHFSplit_BDTGT0p2/hists_WenHighPt.root'),
            'Wmn': PrefitFile('VZcombo_7_3/WlnZbb_Datacards_April6_v2_BTFullDecorr_WHFSplit_BDTGT0p2/hists_WmnHighPt.root'),
            'ZeeLowPt': PrefitFile('VZcombo_7_3/ZllZbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zee_LowPt.root'),
            'ZmmLowPt': PrefitFile('VZcombo_7_3/ZllZbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zuu_LowPt.root'),
            'ZeeHighPt': PrefitFile('VZcombo_7_3/ZllZbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zee_HighPt.root'),
            'ZmmHighPt': PrefitFile('VZcombo_7_3/ZllZbb_Datacards_Minus08to1_JECfix_7_3/vhbb_TH_BDT_Zuu_HighPt.root'),
        },
        'mlfit': MlfitFile('VZcombo_7_3/mlfit.root'),
    }

    MLFIT_DIRECTORIES = {
        'Znn': 'shapes_fit_s/ZnnHbb_ZnnHbb_Signal',
        'Wen': 'shapes_fit_s/WlnHbb_Wen_SR',
        'Wmn': 'shapes_fit_s/WlnHbb_Wmn_SR',
        'ZeeLowPt': 'shapes_fit_s/ZllHbb_ch2_Zee_SIG_low',
        'ZmmLowPt': 'shapes_fit_s/ZllHbb_ch1_Zmm_SIG_low',
        'ZeeHighPt': 'shapes_fit_s/ZllHbb_ch4_Zee_SIG_high',
        'ZmmHighPt': 'shapes_fit_s/ZllHbb_ch3_Zmm_SIG_high',
    }


    outfile = ROOT.TFile.Open('fit_shapes.root', 'recreate')
    for analysis in [VH, VZ]:
        data_copy, x_bins = {}, {}
        for channel_bin, prefit_file in analysis['prefit'].iteritems():
            shapes = prefit_file.get_shapes()
            x_bins[channel_bin] = get_x_bins(shapes[0])
            data_copy[channel_bin] = [shape for shape in shapes if shape.GetName() == 'data_obs'][0]
            outdir = '{0}/prefit/{1}'.format(analysis['name'], channel_bin)
            write_objects(shapes, outfile, outdir)
        for channel_bin, indir in MLFIT_DIRECTORIES.iteritems():
            shapes = analysis['mlfit'].get_shapes(indir, x_bins[channel_bin])
            shapes.append(data_copy[channel_bin])
            outdir = '{0}/postfit/{1}'.format(analysis['name'], channel_bin)
            write_objects(shapes, outfile, outdir)
    outfile.Close()

