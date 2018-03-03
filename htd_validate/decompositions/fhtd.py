import logging
from cStringIO import StringIO

import networkx as nx
from htd_validate.decompositions import GeneralizedHypertreeDecomposition
from htd_validate.utils import Hypergraph


class FractionalHypertreeDecomposition(GeneralizedHypertreeDecomposition):
    _problem_string = 'fhtd'
    _data_type = float

    @staticmethod
    def decomposition_type():
        pass

    @staticmethod
    def from_ordering(hypergraph, ordering=None, weights=None):
        if ordering is None:
            ordering = sorted(hypergraph.nodes())
        logging.debug("Ordering: %s" % ordering)

        tree = nx.DiGraph()
        # use lex smallest, python first compares first pos of tuple
        smallest = lambda x: min([(ordering.index(xi), xi) for xi in x])

        # initialize with empty bags
        chi = {v: set() for v in hypergraph.nodes()}
        tree.add_nodes_from(range(1, hypergraph.number_of_nodes() + 1))

        for e in hypergraph.edges():
            chi[smallest(e)[1]].update(e)

        for v in ordering:
            # copy
            A = set(chi[v])  # - v

            if len(A) > 1:
                logging.debug("A(pre-rem) = %s" % A)
                A.remove(v)
                logging.debug("A(post-rem) =%s" % A)
                nxt = smallest(A)[1]
                logging.debug("nxt= %s,v=%s,A=%s,chi[nxt]=%s" % (nxt, v, A, chi[nxt]))
                chi[nxt].update(A)
                logging.debug("chi[nxt]=%s" % chi[nxt])
                tree.add_edge(nxt, v)

        return FractionalHypertreeDecomposition(plot_if_td_invalid=True, tree=tree, bags=chi, hypergraph=hypergraph,
                                                hyperedge_function=weights)

    # @staticmethod
    # def _reader(decomp, line):
    #    if line[0] == 'w':
    #        decomp.hyperedge_function[int(line[1])][int(line[2])] = float(line[3])
    #        return True
    #    return False

    @staticmethod
    def graph_type():
        return Hypergraph.__name__

    def __init__(self, plot_if_td_invalid=False, tree=None, bags=None, hypergraph=None, hyperedge_function=None):
        super(FractionalHypertreeDecomposition, self).__init__(tree, bags, hypergraph, hyperedge_function)
        self.plot_if_td_invalid = plot_if_td_invalid

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
