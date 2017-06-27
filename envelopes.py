import sys

import ROOT
import numpy


MC_STYLE = {
    'Signal': (ROOT.kRed, 12.0),
    'TT': (ROOT.kBlue, 150.0),
    'Zj2b': (ROOT.kOrange, 60.0),
}


def set_style():
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptTitle(0)
    ROOT.gStyle.SetPadTopMargin(0.05)
    ROOT.gStyle.SetPadBottomMargin(0.13)
    ROOT.gStyle.SetPadLeftMargin(0.15)
    ROOT.gStyle.SetPadRightMargin(0.04)
    ROOT.gStyle.SetTitleColor(1, 'XYZ')
    ROOT.gStyle.SetTitleFont(42, 'XYZ')
    ROOT.gStyle.SetTitleSize(0.05, 'XYZ')
    ROOT.gStyle.SetTitleXOffset(1.05)
    ROOT.gStyle.SetTitleYOffset(1.45)
    ROOT.gStyle.SetLabelColor(1, 'XYZ')
    ROOT.gStyle.SetLabelFont(42, 'XYZ')
    ROOT.gStyle.SetLabelOffset(0.007, 'XYZ')
    ROOT.gStyle.SetLabelSize(0.035, 'XYZ')
    ROOT.gStyle.SetAxisColor(1, 'XYZ')
    ROOT.gStyle.SetStripDecimals(ROOT.kTRUE)
    ROOT.gStyle.SetTickLength(0.03, 'XYZ')
    ROOT.gStyle.SetNdivisions(510, 'XYZ')
    ROOT.gStyle.SetPadTickX(1)
    ROOT.gStyle.SetPadTickY(1)
    ROOT.gStyle.SetPaperSize(20., 20.)


def get_syst_envelope(nominal, shapes):
    n_bins = nominal.GetNbinsX()
    x = numpy.array([nominal.GetBinCenter(i) for i in xrange(1, n_bins + 1)], dtype=numpy.float64)
    y = numpy.array([nominal.GetBinContent(i) for i in xrange(1, n_bins + 1)], dtype=numpy.float64)
    max_binwise_deviation = numpy.array(
        [max(abs(shape.GetBinContent(i) - nominal.GetBinContent(i)) for shape in shapes) for i in xrange(1, n_bins + 1)],
        dtype=numpy.float64,
    )
    # If there are no errors in the x-direction, the fill area doesn't behave correctly.
    # Set dummy x errors as half a bin width.
    bin_width = nominal.GetXaxis().GetBinWidth(1)
    dummy_x_errors = numpy.array([bin_width/2.] * n_bins, dtype=numpy.float64)
    syst_envelope = ROOT.TGraphErrors(n_bins, x, y, dummy_x_errors, max_binwise_deviation)
    return syst_envelope


def make_syst_envelope_plot(nominal, syst_envelope, color, header_text, filename):
    c = ROOT.TCanvas(filename, '', 600, 600)
    c.SetFillStyle(4000)
    c.SetFrameFillStyle(1000)
    c.SetFrameFillColor(0)
    if nominal.GetMaximumBin() > nominal.GetNbinsX() / 2:
        l = ROOT.TLegend(0.2, 0.75, 0.35, 0.9)
    else:
        l = ROOT.TLegend(0.55, 0.75, 0.7, 0.9)
    l.SetFillColor(0)
    l.SetLineColor(0)
    l.SetShadowColor(0)
    l.SetTextFont(62)
    l.SetTextSize(0.025)
    l.SetBorderSize(1)
    l.SetHeader(header_text)
    nominal.SetLineColor(color)
    nominal.SetLineWidth(2)
    nominal.SetAxisRange(-0.8, 1.0, 'x')
    nominal.GetXaxis().SetTitle('BDT')
    nominal.GetYaxis().SetTitle('Events / 0.05')
    nominal.GetYaxis().SetTitleOffset(1.5)
    nominal.Draw('hist')
    l.AddEntry(nominal, 'Nominal', 'L')
    syst_envelope.SetFillColorAlpha(color, 0.35)
    syst_envelope.Draw('2 same')
    l.AddEntry(syst_envelope, 'Systematics Envelope', 'F')
    l.Draw()
    c.Update()
    c.RedrawAxis()
    c.SaveAs(filename + '.pdf')


def process_file(path, tag):
    f = ROOT.TFile.Open(path)
    if tag == 'highsig':
        header_text = 'Prefit Significance = 1.5863'
    elif tag == 'lowsig':
        header_text = 'Prefit Significance = 1.09464'
    else:
        header_text = tag
    keys = {key.GetName(): key for key in f.Znn_13TeV_Signal.GetListOfKeys()}
    # b-Tagging Systematics Envelope
    btag_shapes = {name: key.ReadObj() for name, key in keys.iteritems() if 'bTag' in name}
    for process, (color, y_max) in MC_STYLE.iteritems():
        if process == 'Signal':
            nominal_ZH_hbb = f.Get('Znn_13TeV_Signal/ZH_hbb')
            nominal_ggZH_hbb = f.Get('Znn_13TeV_Signal/ggZH_hbb')
            nominal_WH_hbb = f.Get('Znn_13TeV_Signal/WH_hbb')
            nominal = nominal_ZH_hbb + nominal_ggZH_hbb + nominal_WH_hbb
            shapes_ZH_hbb = [btag_shapes[name] for name in sorted(btag_shapes) if 'ZH_hbb' in name and not 'gg' in name]
            shapes_ggZH_hbb = [btag_shapes[name] for name in sorted(btag_shapes) if 'ggZH_hbb' in name]
            shapes_WH_hbb = [btag_shapes[name] for name in sorted(btag_shapes) if 'WH_hbb' in name]
            shapes = [h1 + h2 +h3 for h1, h2, h3 in zip(shapes_ZH_hbb, shapes_ggZH_hbb, shapes_WH_hbb)]
        else:
            nominal = f.Get('Znn_13TeV_Signal/{}'.format(process))
            shapes = [btag_shapes[name] for name in sorted(btag_shapes) if process in name]
        nominal.SetMaximum(y_max)
        btag_syst_envelope = get_syst_envelope(nominal, shapes)
        filename = '{}_btag_syst_envelope_{}'.format(tag, process)
        make_syst_envelope_plot(nominal, btag_syst_envelope, color, header_text, filename)
    # Factorized JEC Systematics Envelope
    jec_shapes = {name: key.ReadObj() for name, key in keys.iteritems() if 'scale_j' in name}
    for process, (color, y_max) in MC_STYLE.iteritems():
        if process == 'Signal':
            nominal_ZH_hbb = f.Get('Znn_13TeV_Signal/ZH_hbb')
            nominal_ggZH_hbb = f.Get('Znn_13TeV_Signal/ggZH_hbb')
            nominal_WH_hbb = f.Get('Znn_13TeV_Signal/WH_hbb')
            nominal = nominal_ZH_hbb + nominal_ggZH_hbb + nominal_WH_hbb
            shapes_ZH_hbb = [jec_shapes[name] for name in sorted(jec_shapes) if 'ZH_hbb' in name and not 'gg' in name]
            shapes_ggZH_hbb = [jec_shapes[name] for name in sorted(jec_shapes) if 'ggZH_hbb' in name]
            shapes_WH_hbb = [jec_shapes[name] for name in sorted(jec_shapes) if 'WH_hbb' in name]
            shapes = [h1 + h2 +h3 for h1, h2, h3 in zip(shapes_ZH_hbb, shapes_ggZH_hbb, shapes_WH_hbb)]
        else:
            nominal = f.Get('Znn_13TeV_Signal/{}'.format(process))
            shapes = [jec_shapes[name] for name in sorted(jec_shapes) if process in name]
        nominal.SetMaximum(y_max)
        jec_syst_envelope = get_syst_envelope(nominal, shapes)
        filename = '{}_jec_syst_envelope_{}'.format(tag, process)
        make_syst_envelope_plot(nominal, jec_syst_envelope, color, header_text, filename)
    f.Close()


def main():
    ROOT.gROOT.SetBatch(True)
    set_style()
    process_file('ZnnHbb_Datacards_Jun18_OldishApril25BDT_Minus0p8_to_Plus1/vhbb_TH_Znn_13TeV_Signal.root', 'highsig')
    process_file('ZnnHbb_Datacards_Jun18_OldOldBDT_Minus0p8_to_Plus1/vhbb_TH_Znn_13TeV_Signal.root', 'lowsig')


if __name__ == '__main__':

    status = main()
    sys.exit(status)

