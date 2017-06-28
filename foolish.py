import sys

from rootpy.io import root_open


# As opportunity arose in the analysis,
# try the rootpy way of adding branches.

def add_complicated_branch(path):
    passing_list = []
    # First open the file for reading and compute the values.
    with root_open(path) as f:
        t = f.Get('tree')
        for i, entry in enumerate(t):
            if i % 10000 == 0:
                print i
            passing_list.append(entry.HLT_BIT_HLT_PFMET110_PFMHT110_IDTight_v
                                or entry.HLT_BIT_HLT_PFMET120_PFMHT120_IDTight_v
                                or entry.HLT_BIT_HLT_PFMET170_NoiseCleaned_v
                                or entry.HLT_BIT_HLT_PFMET170_HBHE_BeamHaloCleaned_v
                                or entry.HLT_BIT_HLT_PFMET170_HBHECleaned_v)
    # Then open the file for updating and write the computed values.
    with root_open(sys.argv[1], 'UPDATE') as f:
        t = f.Get('tree')
        t.create_branches({'passing_triggers': 'I'})
        b = t.GetBranch('passing_triggers')
        for i, (entry, passing) in enumerate(zip(t, passing_list)):
            if i % 10000 == 0:
                print i
            entry.passing_triggers = passing
            b.Fill()
        t.Write()


def add_is_ZH(path):
    """Append a branch which holds an integer for determining
    whether an ntuple is signal ZH (1) or something else (0).
    """
    with root_open(path, 'a') as f:
        t = f.Get('tree')
        t.create_branches({'is_ZH': 'I'})
        b = t.GetBranch('is_ZH')
        for i, entry in enumerate(t):
            if i % 10000 == 0:
                print i
            entry.is_ZH = 0
            b.Fill()
        t.Write()

