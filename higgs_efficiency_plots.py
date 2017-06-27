import functools
import os
import sys

import CMS_lumi
import ROOT
import tdrstyle

# You'll need to download the CMS_lumi and tdrstyle modules provided
# by the Publications Committee here https://ghm.web.cern.ch/ghm/plots/


ROOT.gROOT.ProcessLine("""
#include "TMath.h"
#include "TVector2.h"

bool isdRMatch(float threshold, float eta1, float phi1, float eta2, float phi2) {
  float dEta = eta1 - eta2;
  double dPhi = TVector2::Phi_mpi_pi(phi1 - phi2);
  if (TMath::Sqrt(dEta*dEta + dPhi*dPhi) < threshold) {
    return true;
  } else {
    return false;
  }
}
""")


def main():
    ROOT.gROOT.SetBatch(True)
    f = ROOT.TFile.Open(sys.argv[1])
    t = f.Get('tree')
    eff_csv = ROOT.TEfficiency('h_csv', 'Highest CSV Higgs;p_{T}(V) (GeV);Efficiency', 20, 0, 500)
    eff_dijet = ROOT.TEfficiency('h_dijet', 'Highest Dijet Higgs;p_{T}(V) (GeV);Efficiency', 20, 0, 500)
    # Creating references to instance methods avoids spending time on attribute lookup in the for loop.
    fill_csv = eff_csv.Fill
    fill_dijet = eff_dijet.Fill
    # Preload threshold value for simplified function call.
    isdRMatch = functools.partial(ROOT.isdRMatch, 0.5)
    for i, e in enumerate(t):
        if i % 10000 == 0:
            print 'Processing event {!s}'.format(i)
        # Generator level selection cuts.
        min_GenBQuarkFromH_pt = min(e.GenBQuarkFromH_pt[0], e.GenBQuarkFromH_pt[1])
        max_abs_GenBQuarkFromH_eta = max(abs(e.GenBQuarkFromH_eta[0]), abs(e.GenBQuarkFromH_eta[1]))
        if min_GenBQuarkFromH_pt < 20 or max_abs_GenBQuarkFromH_eta > 2.5:
            continue
        # Higgs candidate dR matching. Note that GenHiggsBoson is a PyFloatBuffer,
        # so it must be accessed by index as opposed to the Higgs candidate.
        match_csv = isdRMatch(e.GenHiggsBoson_eta[0], e.GenHiggsBoson_phi[0], e.HCSV_eta, e.HCSV_phi)
        fill_csv(match_csv, e.V_pt)
        match_dijet = isdRMatch(e.GenHiggsBoson_eta[0], e.GenHiggsBoson_phi[0], e.H_eta, e.H_phi)
        fill_dijet(match_dijet, e.V_pt)
    # Format plotting style.
    tdrstyle.setTDRStyle()
    CMS_lumi.extraText = 'Simulation'
    CMS_lumi.lumi_sqrtS = '13 TeV'
    c = ROOT.TCanvas('c', 'c', 50, 50, 800, 600)
    c.SetFillColor(0)
    c.SetBorderMode(0)
    c.SetFrameFillStyle(0)
    c.SetFrameBorderMode(0)
    c.SetLeftMargin(0.12)
    c.SetRightMargin(0.04)
    c.SetTopMargin(0.08)
    c.SetBottomMargin(0.12)
    c.SetTickx(0)
    c.SetTicky(0)
    eff_csv.SetLineColor(ROOT.kRed)
    eff_csv.SetFillColor(ROOT.kRed)
    eff_csv.Draw()
    eff_dijet.SetLineColor(ROOT.kBlue)
    eff_dijet.SetFillColor(ROOT.kBlue)
    eff_dijet.Draw('same')
    ROOT.gPad.Update()
    graph_csv = eff_csv.GetPaintedGraph()
    graph_dijet = eff_dijet.GetPaintedGraph()
    graph_csv.SetMaximum(1.3)
    x_axis = graph_csv.GetXaxis()
    line_unity = ROOT.TLine(x_axis.GetXmin(), 1, x_axis.GetXmax(), 1)
    line_unity.SetLineStyle(2)
    line_unity.Draw('same')
    y_axis = graph_csv.GetYaxis()
    y_axis.SetTitleOffset(1)
    legend = ROOT.TLegend(0.75, 0.18, 0.95, 0.35)
    legend.SetFillStyle(0)
    legend.AddEntry(graph_csv, 'Highest CSV', 'le')
    legend.AddEntry(graph_dijet, 'Highest Dijet', 'le')
    legend.Draw('same')
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(42)
    latex.SetTextAngle(0)
    latex.SetTextColor(ROOT.kBlack)
    latex.SetTextSize(0.57 * ROOT.gPad.GetTopMargin())
    latex.SetTextAlign(12)
    latex.DrawLatex(0.78, 0.88, 'WH #rightarrow l#nu b#bar{b}')
    CMS_lumi.CMS_lumi(pad=c, iPeriod=0, iPosX=11)
    c.cd()
    c.Update()
    c.RedrawAxis()
    frame = c.GetFrame()
    frame.Draw()
    c.SaveAs('higgs_efficiency_WlnH.png')
    c.SaveAs('higgs_efficiency_WlnH.pdf')
    f.Close()

if __name__ == '__main__':

    status = main()
    sys.exit(status)

