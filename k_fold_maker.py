import ROOT
import numpy

# More ideas:
# Return the 'k' folds as numpy arrays for Theano?
# Save the 'k' folds as .mat or .npy binaries for reproducibility and portability?
# If there are an imbalance of classes, stratify the sampling for the folds?

def set_dtype(tree, branch_name):
    pass


def create_k_folds(input_root_file_name, input_tree_name=None, k_folds=None):
    """Inspect a .root ntuple and resample a TTree into k-folds for cross-validation.
    """
    input_root_file = ROOT.TFile(input_root_file_name)
    # Check function arguments.
    if not input_tree_name or not input_root_file.GetListOfKeys().FindObject(input_tree_name):
        # Could've thrown an exception here rather than a print statement.
        print "Unspecified or incorrect TTree name. Consider the file contents below.\n"
        input_root_file.ls()
        return
    elif k_folds is None:
        print "\nUnspecified number of folds."
        return
    else:
        input_tree = input_root_file.Get(input_tree_name)
        input_tree_n_entries = input_tree.GetEntriesFast()
    # Specify output directory, creating it if it doesn't exist.
    output_directory = 'k_folds/'
    if (ROOT.gSystem.AccessPathName(output_directory)):
        ROOT.gSystem.mkdir(output_directory)
    # Determine the number of entries per fold, assuming the total number of entries is exactly divisible into k folds.
    # Create a list holding the entry indices specifying the endpoints for each fold.
    n_entries_per_fold = int(input_tree_n_entries / k_folds)
    range_list = range(0, n_entries_per_fold * (k_folds + 1), n_entries_per_fold)
    # If a remainder exists, we modify accordingly.
    n_entries_remainder = int(input_tree_n_entries % k_folds)
    if n_entries_remainder != 0:
        for extra in xrange(len(range_list)):
            if extra < n_entries_remainder:
                range_list[extra] += extra
            else:
                range_list[extra] += n_entries_remainder
    # Loop over each fold.
    for k in xrange(k_folds):
        # Create output .root file for the current fold.
        output_root_file_name = output_directory + 'CVFold_%s_of_%s.root' % (k+1, k_folds)
        output_root_file = TFile(output_root_file_name, 'RECREATE')
        # Copy an empty tree to hold the training sample.
        output_train_tree = input_tree.CloneTree(0)
        output_train_tree.SetName('%s_CV_Train' % input_tree.GetName())
        # Copy an empty tree to hold the "testing" sample.
        output_test_tree = input_tree.CloneTree(0)
        output_test_tree.SetName('%s_CV_Test' % input_tree.GetName())
        # Loop over the input tree entries, storing it for testing if it falls within the range
        # and training otherwise. I find this faster than conditionals within the loop.
        for entry in xrange(range_list[k]):
            input_tree.GetEntry(entry, 1) # The second argument 1 means get all branches.
            output_train_tree.Fill()
        for entry in xrange(range_list[k], range_list[k+1]):
            input_tree.GetEntry(entry, 1)
            output_test_tree.Fill()
        for entry in xrange(range_list[k+1], input_tree_n_entries):
            input_tree.GetEntry(entry, 1)
            output_train_tree.Fill()
        # Write the output trees and save the output file.
        output_train_tree.Write()
        output_test_tree.Write()
        output_root_file.Close()
    # Close the input file.
    input_root_file.Close()
    # Future Sean cringes at lack of logging.
    return "Successfully split entries for %s-fold cross-validation." % k_folds

