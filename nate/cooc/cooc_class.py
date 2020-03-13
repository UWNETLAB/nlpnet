from ..edgeburst.burst_detection import bursts, detect_bursts
from ..edgeburst.export import df_export, max_bursts_export, all_bursts_export, offsets_export
from typing import List, Dict
import pickle
from ..utils.mp_helpers import mp

class cooc():
    """
    This is a docstring
    """
    def __init__(self, offset_dict, lookup, minimum_offsets = 20):
        self.offset_dict = offset_dict
        self.lookup = lookup
        self.minimum_offsets = minimum_offsets

    def burst_detection(self, s:float = 2, gamma:float = 1):
        """
        Returns an object of the class `bursts`

        This method is used to detect bursts for _all_ of the term-term pairs in the offset dictionary generated when this class (`edge_burst`) was instantiated.
        This method is best employed as an exploratory tool for identifying unusually bursty term pairs, or groups of term pairs with correlated burst patterns.  

        Since calling this method on an entire dataset can consume significant amounts of time and memory, this method only allows for one value of s and one value of gamma.

        If you wish to detect bursts using a variety of different values for the s and gamma parameters, instead utilize the `multi_bursts` method contained in this class. 
        """
        offset_dict_strings = offsets_export(self.offset_dict, self.lookup)
        edge_burst_dict_int = detect_bursts(self.offset_dict, s, gamma)
        edge_burst_dict_strings = all_bursts_export(edge_burst_dict_int, self.offset_dict, self.lookup)

        return bursts(offset_dict_strings, edge_burst_dict_strings, s, gamma)


    def multi_burst(self, token_pairs:List, s:List, gamma:List) -> Dict:
        """
        The lists passed to s and gamma must be exactly the same length.

        Returns a dictionary where keys are strings containing two numbers separated by an underscore, corresponding to the s and gamma values for the run, respectively.
        The values of each entry in the dictionary consists of {SOMETHING}
        """
        assert len(s) == len(gamma)

        run_dict = {}
        offset_subset_dict = {}

        for token_pair in token_pairs:
            offset_subset_dict[token_pair] = self.offset_dict[token_pair]

        for i in range(0,len(s)):
            run_name = "{}_{}".format(str(s[i]), str(gamma[i]))
            run_result = bursts(self.offset_dict,self.lookup, s[i], gamma[i])
            run_dict[run_name] = run_result

        return run_dict