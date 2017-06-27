import ROOT
import numpy as np


class BranchAddresses(object):
    """Automatically set branch addresses for ROOT TTrees.

    Parameters
    ----------
    root_file : ROOT.TFile
        The open TFile.
    tree : str
        The name of the TTree to access within the file.
    leaves : iterable of strings, optional
        The names of the TLeaf's to access within the tree.
        The default is an empty list for all leaves.
    """

    NUMPY_DTYPES_MAP = {
        'Bool_t': np.bool,
        'Char_t': np.int8,
        'UChar_t': np.uint8,
        'Short_t': np.int16,
        'UShort_t': np.uint16,
        'Int_t': np.int32,
        'UInt_t': np.uint32,
        'Float_t': np.float32,
        'Double_t': np.float64,
        'Long64_t': np.int64,
        'ULong64_t': np.uint64,
    }

    def __init__(self, root_file, tree, leaves=[]):
        self.tree = self.root_file.Get(tree)
        self.branches = []
        if not leaves:
            leaves = [leaf.GetName() for leaf in self.tree.GetListOfLeaves()]
        self._set_branch_addresses(leaves)

    def _set_branch_addresses(self, leaves):
        """For each TLeaf, create an appropriately sized and typed numpy array attribute
        named after its TBranch, then set it as its branch address.
        ROOT to NumPy Type Conversion
        (http://rootpy.github.io/root_numpy/reference/index.html#type-conversion-table)
        """
        for name in leaves:
            leaf = self.tree.GetLeaf(name)
            leaf_dtype = self.NUMPY_DTYPES_MAP[leaf.GetTypeName()]
            leaf_size = leaf.GetNdata()
            setattr(self, name, np.zeros(leaf_size, dtype=leaf_type))
            branch_name = leaf.GetBranch().GetName()
            self.branches.append(branch_name)
            self.tree.SetBranchAddress(branch_name, getattr(self, name))
            # If the leaf is indexed by another leaf that isn't present in the list,
            # append it to the end of the list so that it gets a branch address too.
            if leaf.GetLeafCount():
                leaf_counter = leaf.GetLeafCount().GetName()
                if leaf_counter not in leaves:
                    leaves.append(leaf_counter)

