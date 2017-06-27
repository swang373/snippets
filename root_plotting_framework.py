import collections
import itertools

import ROOT


class PlottingFramework(object):
    """Example of a class which encapsulates the logic for generating a ROOT plot.
    There are better ways of going about this sort of thing. I've tidied it up a
    little and use it to critique myself.

    Parameters
    ----------
    logy : bool, optional
        Whether the y-axis is logarithmic. This setting is tied to the canvas,
        so it must be an initialization parameter. The default is False.
    split : bool, optional
        Whether the canvas is split into an upper and lower pad.
        The default is False.
    """
    def __init__(self, logy=False, split=False):
        self.canvas = ROOT.TCanvas('canvas', '', 700, 700)
        self.logy = logy
        self.split = split
        if self.split:
            self.upper_pad = ROOT.TPad('upper_pad', '', 0.0, 0.3, 1.0, 1.0)
            self.upper_pad.SetBottomMargin(0.0)
            self.upper_pad.Draw()
            self.lower_pad = ROOT.TPad('lower_pad', '', 0.0, 0.0, 1.0, 0.3)
            self.lower_pad.SetBottomMargin(0.35)
            self.lower_pad.SetTopMargin(0.0)
            self.lower_pad.Draw()
            # Switch the active pad to the upper pad.
            self.upper_pad.cd()
            self.upper_pad.SetLogy(self.logy)
        else:
            self.canvas.SetLogy(self.logy)

    def project(self, trees, htype='F', exps=[], cuts=[], n_xbins=None, x_min=None, x_max=None):
        """
        Parameters
        ----------
        trees : collections.OrderedDict with string keys and ROOT.TTree values
            For each TTree, pass the label to appear in the TLegend as the key.
            Note that ROOT has some support for LaTeX style formatting.
        htype : str
            The histogram type to be projected onto, e.g. 'I' for Int_t,
            'F' for Float_t, or 'D' for Double_t. The default is 'F'.
        exps : list of strings
            A TTreeFormula expression defining what is to be projected onto the
            histogram. Refer to the documentation of TTree.Draw() for usage.
            If a single expression is passed, it is broadcasted to all TTrees.
        cuts : list of strings
            A TTreeFormula expression defining a selection over the TTree
            entries. The subset of entries passing the selection fill the plot.
            If a single selection is passed, it is broadcasted to all TTrees.
        n_xbins : int
            The number of bins along the x-axis.
        x_min : float
            The lower bound of the x-axis.
        x_max : float
            The upper bound of the x-axis.
        """
        self.trees = trees
        # Save the x-axis information.
        self.n_xbins = n_xbins
        self.x_min = x_min
        self.x_max = x_max
        # Histogram Type
        assert(htype in ['I', 'F', 'D'])
        # TTree.Project Expressions and Cuts
        n_trees = len(self.trees)
        if (len(exps) == 1):
            exps = exps * n_trees
        if (len(cuts) == 1):
            cuts = cuts * n_trees
        # OrderedDict of Histograms.
        self.hists = collections.OrderedDict()
        # Project Expressions
        for tree, exp, cut in zip(self.trees, exps, cuts):
            i = len(self.hists)
            # Instantiate a histogram of the correct type.
            if (htype == 'I'):
                self.hists[tree] = ROOT.TH1I(('h_%s' % i), exp, n_xbins, x_min, x_max)
            elif (htype == 'F'):
                self.hists[tree] = ROOT.TH1F(('h_%s' % i), exp, n_xbins, x_min, x_max)
            elif (htype == 'D'):
                self.hists[tree] = ROOT.TH1D(('h_%s' % i), exp, n_xbins, x_min, x_max)
            self.trees[tree].Project(('h_%s' % i), exp, cut)

    def draw(self, name='', hists=None, x_label='', y_label='', style=''):
        """
        Parameters
        ----------
        name : str
            Unique string to identify the THStack instance.
        hists : list, [str, ...]
            A list of histograms to be drawn for this given stack instance,
            referenced by their key in self.hists.
        x_label : str
            The formatted x-axis title.
        y_label : str
            The formatted y-axis title.
        style : str
            The draw style of the THStack. For accepted options, consult
            root.cern.ch/doc/master/classTHistPainter.html#HP01.
        """
        # Save the axis labels.
        if x_label:
            self.x_label = x_label
        if y_label:
            self.y_label = y_label
        # Instantiate THStack
        setattr(self, name, ROOT.THStack('THStack_' + name, ''))
        if not hasattr(self, 'first_stack'):
            setattr(self, 'first_stack', name)
        hist_stack = getattr(self, name)
        for x in hists:
            hist_stack.Add(self.hists[x])
        hist_stack.Draw(style)
        # Set x-axis label.
        hist_stack.GetXaxis().SetTitle(self.x_label)
        # Set y-axis label.
        hist_stack.GetYaxis().SetTitle(self.y_label)
        # Depending on the y-axis scale, adjust range for viewing.
        if self.logy:
            y_max = 10**(ROOT.gPad.GetUymax())
            hist_stack.SetMaximum(y_max * 13.5)
        else:
            fstack = getattr(self, getattr(self, 'first_stack'))
            if hist_stack.GetMaximum() >= fstack.GetMaximum():
                y_max = ROOT.gPad.GetUymax()
                fstack.SetMaximum(y_max * 1.2)

    def legend(self, name='', x1=0.0, y1=0.0, x2=0.0, y2=0.0, entries=[], styles=['l'], font_size=0.03):
        """
        Parameters
        ----------
        name : str
            Unique string to identify the TLegend instance.
        x1 : float
            The normalized canvas x-coordinate of the lower left-hand corner.
        y1 : float
            The normalized canvas y-coordinate of the lower left-hand corner.
        x2 : float
            The normalized canvas x-coordinate of the upper right-hand corner.
        y2 : float
            The normalized canvas y-coordinate of the upper right-hand corner.
        entries : list of strings
            The legend entries to be added to this legend instance. The string
            items must be a valid key of self.hists.
            The default is [], which adds an entry for all histograms.
        styles : list of strings
            The visual style of the legend entry for each respective histogram.
            Passing a single item applies the same style to each entry.
            The default is ['l'] for line style. Consult the documentation for
            TLegend::AddEntry for other styles.
        font_size : float
            The font size to be used for the legend text.
        """
        # Instantiate TLegend
        setattr(self, name, ROOT.TLegend(x1, y1, x2, y2))
        # Legend Settings
        leg = getattr(self, name)
        leg.SetFillColor(0)
        leg.SetLineColor(0)
        leg.SetShadowColor(0)
        leg.SetTextFont(62)
        leg.SetTextSize(font_size)
        leg.SetBorderSize(1)
        if not entries:
            entries = [x for x in self.hists]
        for x in itertools.izip_longest(entries, styles, fillvalue = styles[0]):
            leg.AddEntry(self.hists[x[0]], x[0], x[1])
        leg.Draw('same')

    def latex(self, annotations=[]):
        """
        Parameters
        ----------
        annotations : list of tuples of (float, float, str)
            In each tuple, the first two items specify the normalized
            canvas coordinates for the upper-left corner of the text.
            The third item is the formatted string to be drawn.
            Could've used a namedtuple here.
        """
        # Instantiate TLatex
        self.hist_latex = ROOT.TLatex()
        # LaTeX Settings
        self.hist_latex.SetNDC()
        self.hist_latex.SetTextAlign(12)
        self.hist_latex.SetTextFont(62)
        self.hist_latex.SetTextSize(0.04)
        for x in annotations:
            self.hist_latex.DrawLatex(x[0], x[1], x[2])

    def ratio(self, num='', denom='', small=False):
        """
        Parameters
        ----------
        num : str
            A string matching the key of the histogram to be used as the numerator.
        denom : str
            A string matching the key of the histogram to be used as the denominator.
        small : bool
            Whether or not small font is used for the legend.
        """
        self.ratio = self.hists[num].Clone('ratio')
        self.ratio.Sumw2()
        # Ratio Plot Settings
        self.ratio.SetFillColor(ROOT.kBlack)
        self.ratio.SetLineColor(ROOT.kBlack)
        self.ratio.SetLineWidth(1)
        self.ratio.SetMarkerColor(ROOT.kBlack)
        self.ratio.SetMarkerSize(0.8)
        # Ratio x-axis
        self.ratio.GetXaxis().SetLabelOffset(0.02)
        self.ratio.GetXaxis().SetLabelSize(0.12)
        self.ratio.GetXaxis().SetTitle(self.x_label)
        self.ratio.GetXaxis().SetTitleOffset(1.10)
        self.ratio.GetXaxis().SetTitleSize(0.13)
        # Ratio y-axis
        self.ratio.GetYaxis().SetNdivisions(505)
        self.ratio.GetYaxis().SetLabelSize(0.10)
        #self.ratio.GetYaxis().SetRangeUser(0.0, 2.0)
        self.ratio.GetYaxis().SetTitle('Ratio')
        if small:
            self.ratio.GetYaxis().SetTitleOffset(1.1)
            self.ratio.GetYaxis().SetTitleSize(0.07)
        else:
            self.ratio.GetYaxis().SetTitleOffset(0.6)
            self.ratio.GetYaxis().SetTitleSize(0.13)
        # Calculate Bin-wise Ratio
        for i in range(1, self.n_xbins+1):
            numerator = self.hists[num].GetBinContent(i)
            denominator = self.hists[denom].GetBinContent(i)
            if (denominator == 0):
                self.ratio.SetBinContent(i, 0)
            else:
                self.ratio.SetBinContent(i, numerator / denominator)
        # Draw ratio plot
        self.lower_pad.cd()
        self.ratio.Draw('e1')
        # Draw unity line
        self.unity = ROOT.TLine(self.x_min, 1.0, self.x_max, 1.0)
        self.unity.SetLineStyle(2)
        self.unity.Draw('same')
        # Reset Pads
        self.lower_pad.RedrawAxis()
        self.lower_pad.Modified()
        self.lower_pad.Update()
        self.upper_pad.cd()
        self.upper_pad.RedrawAxis()
        self.upper_pad.Modified()
        self.upper_pad.Update()

    def save(self, outdir='plots/', name='', ext=('.png',)):
        """
        Parameters
        ----------
        outdir : str
            The name of the output directory.
        name : str
            The file name of the saved canvas.
        ext : tuple of strings
            A list of the requested output file types for the saved canvas.
        """
        if self.split:
            self.lower_pad.cd()
            self.lower_pad.RedrawAxis()
            self.lower_pad.Modified()
            self.lower_pad.Update()
            self.upper_pad.cd()
            self.upper_pad.RedrawAxis()
            self.upper_pad.Modified()
            self.upper_pad.Update()
        self.canvas.Update()
        self.canvas.RedrawAxis()
        for x in ext:
            self.canvas.SaveAs(outdir + name + x)
        # Clean Up.
        self.canvas.IsA().Destructor(self.canvas)
        for x in self.hists:
            self.hists[x].IsA().Destructor(self.hists[x])

