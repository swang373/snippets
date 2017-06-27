import logging
import itertools
import os
import sys

import numpy as np
import ROOT


ROOT.gROOT.SetBatch(True)

logging.basicConfig(format='[%(name)s] %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():

    inpath, outpath = sys.argv[1:3]

    logger.info('Input file: %s', inpath)
    logger.info('Output file: %s', outpath)

    infile = ROOT.TFile.Open(inpath)
    outfile = ROOT.TFile.Open(outpath, 'recreate')
    
    # Directly copy any count histograms
    for key in infile.GetListOfKeys():
        if key.GetName() == 'tree':
            continue
        obj = key.ReadObj()
        obj.Write()

    # Clone the input tree
    tree = infile.Get('tree')
    tree_clone = tree.CloneTree(0)
    
    # Setup new systematic branches
    systematic_name_templates = [
        'HCSV_reg_corr{systematic}{variation}_mass_{category}',
        'HCSV_reg_corr{systematic}{variation}_pt_{category}',
        'HCSV_reg_corr{systematic}{variation}_eta_{category}',
        'HCSV_reg_corr{systematic}{variation}_phi_{category}',
        'Jet_pt_reg_corr{systematic}{variation}_{category}',
    ]

    category_definitions = {
        'HighCentral': lambda pt, eta: pt > 100 and abs(eta) < 1.4,
        'LowCentral': lambda pt, eta: pt < 100 and abs(eta) < 1.4,
        'HighForward': lambda pt, eta: pt > 100 and abs(eta) > 1.4,
        'LowForward': lambda pt, eta: pt < 100 and abs(eta) > 1.4,
    }

    modifiers = list(itertools.product(['JEC', 'JER'], ['Up', 'Down'], ['HighCentral', 'LowCentral', 'HighForward', 'LowForward']))

    # Create the new branches, setting their branch addresses to numpy arrays
    branch_addresses = {}
    for template in systematic_name_templates:
        for systematic, variation, category in iter(modifiers):
            name = template.format(**locals())
            if 'Jet' in template:
                branch_addresses[name] = np.zeros(50, dtype=np.float32)
                tree_clone.Branch(name, branch_addresses[name], '{}[nJet]/F'.format(name))                        
            else:
                branch_addresses[name] = np.zeros(1, dtype=np.float32)
                tree_clone.Branch(name, branch_addresses[name], '{}/F'.format(name))
                        
    # Loop over events
    nentries = tree.GetEntriesFast()
    logger.info('Number of entries: %s', nentries)

    for i, event in enumerate(tree):
        if i % 10000 == 0:
            logger.info('Processing event %s', i)
        
        # Set up four vectors for the nominal Higgs and its jets
        higgs_jet_1 = ROOT.TLorentzVector()
        higgs_jet_1.SetPtEtaPhiM(
            event.Jet_pt_reg[event.hJCidx[0]],
            event.Jet_eta[event.hJCidx[0]],
            event.Jet_phi[event.hJCidx[0]],
            event.Jet_mass[event.hJCidx[0]]
        )

        higgs_jet_2 = ROOT.TLorentzVector()
        higgs_jet_2.SetPtEtaPhiM(
            event.Jet_pt_reg[event.hJCidx[1]],
            event.Jet_eta[event.hJCidx[1]],
            event.Jet_phi[event.hJCidx[1]],
            event.Jet_mass[event.hJCidx[1]]
        )

        higgs = higgs_jet_1 + higgs_jet_2

        for systematic, variation, category in iter(modifiers):

            # Set up the four vectors for the systematically varied Higgs and its jets
            higgs_jet_syst_1 = ROOT.TLorentzVector()
            higgs_jet_syst_2 = ROOT.TLorentzVector()

            if category_definitions[category](event.Jet_pt_reg[event.hJCidx[0]], event.Jet_eta[event.hJCidx[0]]):
                higgs_jet_syst_1.SetPtEtaPhiM(
                    getattr(event, 'Jet_pt_reg_corr{systematic}{variation}'.format(**locals()))[event.hJCidx[0]],
                    event.Jet_eta[event.hJCidx[0]],
                    event.Jet_phi[event.hJCidx[0]],
                    event.Jet_mass[event.hJCidx[0]]
                )
            else:
                higgs_jet_syst_1 = higgs_jet_1
        
            if category_definitions[category](event.Jet_pt_reg[event.hJCidx[1]], event.Jet_eta[event.hJCidx[1]]):
                higgs_jet_syst_2.SetPtEtaPhiM(
                    getattr(event, 'Jet_pt_reg_corr{systematic}{variation}'.format(**locals()))[event.hJCidx[1]],
                    event.Jet_eta[event.hJCidx[1]],
                    event.Jet_phi[event.hJCidx[1]],
                    event.Jet_mass[event.hJCidx[1]]
                )
            else:
                higgs_jet_syst_2 = higgs_jet_2

            higgs_syst = higgs_jet_syst_1 + higgs_jet_syst_2

            # Assign newly calculated values to branch addresses
            branch_addresses['HCSV_reg_corr{systematic}{variation}_mass_{category}'.format(**locals())][0] = event.HCSV_reg_mass * (higgs_syst.M()/higgs.M())
            branch_addresses['HCSV_reg_corr{systematic}{variation}_pt_{category}'.format(**locals())][0] = event.HCSV_reg_pt * (higgs_syst.Pt()/higgs.Pt())
            branch_addresses['HCSV_reg_corr{systematic}{variation}_eta_{category}'.format(**locals())][0] = event.HCSV_reg_eta * (higgs_syst.Eta()/higgs.Eta())
            branch_addresses['HCSV_reg_corr{systematic}{variation}_phi_{category}'.format(**locals())][0] = event.HCSV_reg_phi * (higgs_syst.Phi()/higgs.Phi())

            jet_branch_new = 'Jet_pt_reg_corr{systematic}{variation}_{category}'.format(**locals())
            jet_branch_old = 'Jet_pt_reg_corr{systematic}{variation}'.format(**locals())
            for j in xrange(event.nJet):
                if category_definitions[category](event.Jet_pt_reg[j], event.Jet_eta[j]):
                    branch_addresses[jet_branch_new][j] = getattr(tree, jet_branch_old)[j]
                else:
                    branch_addresses[jet_branch_new][j] = event.Jet_pt_reg[j]
          
        tree_clone.Fill()

    # Save the new tree and close the files
    tree_clone.Write()
    outfile.Close()
    infile.Close()


if __name__ == '__main__':

    status = main()
    sys.exit(status)

