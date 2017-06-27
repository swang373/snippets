import collections
import csv
import os
import sys
import warnings

import ROOT
import numpy


def featurize_ntuple(ntuples=[], selection='', feature_dict={}, save_label='file', outfile=('Preprocessed.csv', True)):
    """
    Parameters
    ---------- 
    directory : path
        The absolute path to the ntuples' directory.
    ntuples : list of paths
        The paths of the ntuples to featurize. Automatically generated class
        labels for each ntuple are based on their order in this list.           
    selection : string
        A boolean TTreeFormula expression used to filter examples in 
        the ntuple. For example, for each training event we require
        that the vector boson should be identified as a Z boson and
        either it or the Higgs boson should have transverse momentum
        greater than 80 GeV. One might define the selection expression
        as 'Vtype == 4 && (V_pt > 80 || H_pt > 80)' 
    feature_dict : collections.OrderedDict of string keys and ROOT.TTreeFormula values
        For each feature, pass its name as the key and its TTreeFormula
        expession based on the ntuple's leaves as the value. 
        For compatibility with ROOT, the name must end with '/', followed by
        a data type initial: 'I' for int, 'F' for float, or 'D' for double.     
        e.g. The feature is the transverse momentum of the first jet in a
        collection of jet transverse momenta, 'Jet_pt', with type float. The
        name might be 'Pt_Jet1/F' and its formula expression 'Jet_pt[0]'.
    save_label : string
        Flags whether a class label is included as the first column of the
        .csv file or as a branch in the .root file. The string should be a
        TTreeFormula expression, perhaps pointing to a class label branch.
        In the case of binary classification, a boolean expression can be
        used. Otherwise, pass an empty string to ignore labels.
        The default value 'file' assumes that each ntuple represents a 
        separate class.
    outfile : list of tuples of (string, bool)
        A list describing the output file storing the preprocessing results.
        - The first item is the name, with extension, of the output file.
          Valid file extensions are .csv and .root. Passing an empty string
          creates by default 'ProcessedNtuple.csv'.
        - The second item flags whether a header line, a row concatenating
          the feature names, is written first to the .csv file.
          The default is True.
    """
    # Create the chain of ntuples.
    chain = ROOT.TChain('tree')
    for ntuple in ntuples:
        chain.Add(ntuple)
    # Intialize the selection expression.
    sel = ROOT.TTreeFormula('sel', selection, chain)
    # Initialize the feature expressions.
    exps = [ROOT.TTreeFormula(x, feature_dict[x], chain) for x in feature_dict]
    # Initialize the class label expression, if provided.
    has_label_exp = False
    if save_label and (save_label != 'file'):
        label = ROOT.TTreeFormula('label', save_label, chain)
        has_label_exp = True
    # Parse the output file extension.
    if not outfile[0]:
        outfile[0] = 'ProcessedNtuple.csv'
    print '--- Generating %s with...' % outfile[0]
    print '--- Selection'
    print '---    %s' % selection
    print '--- Features'
    if (save_label == 'file'):
        print '---    %s, %s' % ('Class/I', 'File Number')
    elif has_label_exp:
        print '---    %s, %s' % ('Class/I', save_label)
    for x in feature_dict:
        print '---    %s, %s' % (x, feature_dict[x])
    # Process the chain, saving the output as a .csv file.
    if (outfile[0].endswith('.csv')):
        with open(outfile[0], 'w') as csv_file:
            writer = csv.writer(csv_file)
            # Header Row
            if outfile[1]:
                if save_label:
                    writer.writerow(['Class/I'] + [x for x in feature_dict])
                else:
                    writer.writerow([x for x in feature_dict])
            # Example Rows
            print '--- Processing %s' % os.path.basename(chain.GetFile().GetName())
            fnum = chain.GetTreeNumber()
            for example in chain:
                # Update the file number and TTreeFormulas when the TChain opens the next file.
                if (chain.GetTreeNumber() != fnum):
                    print '--- Processing %s' % os.path.basename(chain.GetFile().GetName())
                    fnum = chain.GetTreeNumber()
                    sel.UpdateFormulaLeaves()
                    for exp in exps:
                        exp.UpdateFormulaLeaves()
                    if has_label_exp:
                        label.UpdateFormulaLeaves()
                # This call is ESSENTIAL for formulae whose leaves have variable size.
                sel.GetNdata()
                for exp in exps:
                    exp.GetNdata()
                if has_label_exp:
                    label.GetNdata()
                if sel.EvalInstance():
                    if (save_label == 'file'):
                        writer.writerow([fnum] + [exp.EvalInstance() for exp in exps])
                    elif has_label_exp:
                        writer.writerow([label.EvalInstance()] + [exp.EvalInstance() for exp in exps])
                    else:
                        writer.writerow([exp.EvalInstance() for exp in exps])
    # Process the chain, saving the output as a .root file.
    elif (outfile[0].endswith('.root')):
        # Create the file and TTree. 
        root_file = ROOT.TFile(outfile[0], 'RECREATE')
        root_tree = ROOT.TTree('features', '')
        # Create branch addresses and TBranches for each feature.
        root_to_np_type = {'I': numpy.int32, 'F': numpy.float32, 'D': numpy.float64}
        if save_label:
            label_address = numpy.array([-999], numpy.int32)
            root_tree.Branch('Class', label_address, 'Class/I')
        branch_addresses = [numpy.array([-999], root_to_np_type[x[-1]]) for x in feature_dict]
        for x, address in zip(feature_dict, branch_addresses):
            root_tree.Branch(x[:-2], address, x)
        # Loop over all entries.
        print '--- Processing %s' % os.path.basename(chain.GetFile().GetName())
        fnum = chain.GetTreeNumber()
        for entry in chain:
            # Update the class label and TTreeFormulas when the TChain opens the next file.
            if (chain.GetTreeNumber() != fnum):
                print '--- Processing %s' % os.path.basename(chain.GetFile().GetName())
                fnum = chain.GetTreeNumber()
                sel.UpdateFormulaLeaves()
                for exp in exps:
                    exp.UpdateFormulaLeaves()
                if has_label_exp:
                    label.UpdateFormulaLeaves()
            # This call is ESSENTIAL for formulae whose leaves have variable size.
            sel.GetNdata()
            for exp in exps:
                exp.GetNdata()
            if has_label_exp:
                label.GetNdata()
            # Fill the branches for each entry.
            if sel.EvalInstance():
                if (save_label == 'file'):
                    label_address[0] = fnum
                elif has_label_exp:
                    label_address[0] = label.EvalInstance()
                for address, exp in zip(branch_addresses, exps):
                    address[0] = exp.EvalInstance()
                root_tree.Fill()
        # Write the TTree and save the file.
        root_file.Write()
        root_file.Close()


def main():
    directory = '/some/directory/'

    ntuples = [
        'skim_ZH_HToBB_ZToNuNu_M125_13TeV_amcatnloFXFX_madspin_pythia8__RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9.root',
        'skim_ggZH_HToBB_ZToNuNu_M125_13TeV_powheg_pythia8__RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9.root',
        'skim_TTJets_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8__RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9.root',
    ]

    selection = 'genWeight > 0 && Vtype == 4 && V_pt > 100'

    feature_dict = collections.OrderedDict([
        ('M_jj/F', 'HCSV_mass'),
        ('Pt_jj/F', 'HCSV_pt'),
        ('Pt_j1/F', 'Jet_pt[hJCidx[0]]'),
        ('Pt_j2/F', 'Jet_pt[hJCidx[1]]'),
        ('Pt_V/F', 'V_pt'),
        ('CSV_max/F', 'Jet_btagCSV[hJCidx[0]]'),
        ('CSV_min/F', 'Jet_btagCSV[hJCidx[1]]'),
    ])

    save_label = 'file' 

    outfile = ('ZnnClassification_skimVpt_posgenWeight_Vtype4.root', True)

    ROOT.gROOT.SetBatch(1)
    # Suppress a PyROOT warning about TTreeFormula.
    warnings.filterwarnings(action = 'ignore', category = RuntimeWarning, message = 'creating converter.*')
    featurize_ntuple([directory + x for x in ntuples], selection, feature_dict, save_label, outfile)

    print "--- Job's done!"


if __name__ == '__main__':

    status = main()
    sys.exit(status)

