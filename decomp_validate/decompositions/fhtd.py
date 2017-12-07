import logging
from collections import defaultdict

from cStringIO import StringIO

from decomp_validate.decompositions import Decomposition
from decomp_validate.decompositions import GeneralizedHypertreeDecomposition
from decomp_validate.utils import Hypergraph


class FractionalHypertreeDecomposition(GeneralizedHypertreeDecomposition):
    @staticmethod
    def decomposition_type():
        pass

    _problem_string = 'fhtd'

    @staticmethod
    def graph_type():
        return Hypergraph.__name__

    def __init__(self, plot_if_td_invalid=False):
        Decomposition.__init__(self)
        self.hypergraph = Hypergraph()
        self.hyperedge_function = defaultdict(dict)

    def __len__(self):
        return len(self.bags)

    # TODO: reading allow floats as well insteat of just integers
    # TODO: technically the same as ghtd, but we skip the integer check
    def validate(self, graph):
        print self.edge_function_holds()
        self.hypergraph = graph
        if self.edges_covered() and self.is_connected() and self.edge_function_holds() and \
                self.edge_function_holds():
            return True
        else:
            logging.error('ERROR in Tree Decomposition.')
            return False

    def __str__(self):
        string = StringIO()
        self.write(string)
        return string.getvalue()
