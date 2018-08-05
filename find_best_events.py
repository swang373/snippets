#!/usr/bin/env python
import root_pandas


class BestEventsFinder(object):
    """Find the best signal region events for each channel by DNN score.

    The signal region definitions are encapsulated by the class. The user
    needs only call an instance with the path to an AnalysisTools ntuple
    and specify the desired channel and DNN branch name.

    Note: The best events are those with the lowest scores because of the
    values contained in the branch are before the "(1 - DNN)" transformation.
    """

    GENERIC_SR = 'Pass_nominal && usingBEnriched && Jet_bReg[hJetInd1]>25 && Jet_bReg[hJetInd2]>25 && controlSample==0'

    CHANNEL_SR = { 
        'Znn': 'isZnn==1 && H_mass>60 && H_mass<160 && hJets_btagged_0>0.8001 && hJets_btagged_1>0.1522',
        'Wen': 'isWenu && (abs(Electron_eta[lepInd1])<1.44 || abs(Electron_eta[lepInd1])>1.56) && V_pt>150 && hJets_btagged_0>0.8001 && hJets_btagged_1>0.1522 && H_mass>90 && H_mass<150',
        'Wmn': 'isWmunu && (abs(Electron_eta[lepInd1])<1.44 || abs(Electron_eta[lepInd1])>1.56) && V_pt>150 && hJets_btagged_0>0.8001 && hJets_btagged_1>0.1522 && H_mass>90 && H_mass<150',
        'Zee': 'isZee && V_pt>50 && hJets_btagged_0>-0.5884 && hJets_btagged_1>-0.5884 && H_mass_fit_fallback>90 && H_mass_fit_fallback<150',
        'Zmm': 'isZmm && V_pt>50 && hJets_btagged_0>-0.5884 && hJets_btagged_1>-0.5884 && H_mass_fit_fallback>90 && H_mass_fit_fallback<150',
    }   

    def __call__(self, path, channel, branch):
        """Report the best events by DNN score.

        Parameters
        ----------
        path : path
            The XRootD url to an AnalysisTools ntuple.
        channel : string
            The channel name which specifies the signal region selection:
              * Znn
              * Wen
              * Wmn
              * Zee
              * Zmm
        branch : string
            The name of the DNN branch used to score events.
        """
        # Form the signal region event selection by combining
        # the generic and channel specific selections.
        selection = '{0} && {1}'.format(self.GENERIC_SR, self.CHANNEL_SR[channel])

        # The list of columns to include in the dataframe.
        columns = [branch, 'run', 'luminosityBlock', 'event']
        df = (
            root_pandas.read_root(path, key='Events', columns=columns, where=selection)
                       .sort_values(by=branch, kind='mergesort')
        )
        print df.head()


if __name__ == '__main__':

    tasks = [
        # tuples of ntuple path, channel name, and DNN branch name
        ('sum_Run2017_MET_MiniAOD.root',         'Znn', 'CMS_vhbb_DNN_Znn_13TeV'),
        ('sum_Run2017_Ele_ReMiniAOD.root',       'Wen', 'CMS_vhbb_DNN_Wen_13TeV'),
        ('sum_Run2017_Mu_ReMiniAOD.root',        'Wmn', 'CMS_vhbb_DNN_Wmn_13TeV'),
        ('sum_Run2017_DoubleEle_ReMiniAOD.root', 'Zee', 'CMS_vhbb_DNN_Zll_LowPT_13TeV'),
        ('sum_Run2017_DoubleEle_ReMiniAOD.root', 'Zee', 'CMS_vhbb_DNN_Zll_HighPT_13TeV'),
        ('sum_Run2017_DoubleMu_ReMiniAOD.root',  'Zmm', 'CMS_vhbb_DNN_Zll_LowPT_13TeV'),
        ('sum_Run2017_DoubleMu_ReMiniAOD.root',  'Zmm', 'CMS_vhbb_DNN_Zll_HighPT_13TeV'),
    ]

    find_best_events = BestEventsFinder()

    for filename, channel, branch in tasks:
        print 'The five best events from {0} for channel {1} as scored by {2} are...'.format(filename, channel, branch)
        path = 'root://cmseos.fnal.gov//store/group/lpchbb/VHbbAnalysisNtuples/2017V5_June19_unblinding/haddjobs/{0}'.format(filename)
        find_best_events(path, channel, branch)
        print '\n'
