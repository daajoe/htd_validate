import logging
from io import StringIO

from htd_validate.decompositions import GeneralizedHypertreeDecomposition
from htd_validate.utils import Hypergraph
from networkx.algorithms.traversal.depth_first_search import dfs_tree


class HypertreeDecomposition(GeneralizedHypertreeDecomposition):
    _problem_string = 'htd'

    @staticmethod
    def decomposition_type():
        pass

    @staticmethod
    def graph_type():
        return Hypergraph.__name__

    def __init__(self, hypergraph=None, tree=None, bags=None, hyperedge_function=None, epsilon=None):
        if epsilon is not None:
            raise TypeError("Tree Decompositions provide exact results. No epsilon expected.")
        super(HypertreeDecomposition, self).__init__(hypergraph=hypergraph, tree=tree, bags=bags,
                                                     hyperedge_function=hyperedge_function)

    def __len__(self):
        return len(self.bags)

    def inverse_edge_function_holds(self):
        logging.info('=' * 80)
        logging.info('Inverse edge function property')
        logging.info('=' * 80)
        for u in self.tree.nodes():
            T_u = dfs_tree(self.tree, u)
            vertices_in_bags_below_u = set()
            for t in T_u.nodes():
                vertices_in_bags_below_u.update(self.bags[t])
            if not (vertices_in_bags_below_u & self._B(u) <= self.bags[u]):
                logging.error('Inverse edge function property does not hold for node "%s"' % u)
                logging.error('Bag of the subtree induced at "%s" contained "%s"' % (u, vertices_in_bags_below_u))
                logging.error('Vertices returned from the edge function are "%s"' % self._B(u))
                logging.error('Bag content is: %s' % self.bags[u])
                logging.error(
                    'Hence, not (vertices_in_bags_below_u & self._B(u) <= self.bags[u]) does not hold for node %s.' % u)
                return False
        logging.info('Inverse edge function property *holds*.')
        logging.info('=' * 80)
        return True

    def validate(self, graph, strict=True):
        self.hypergraph = graph
        if self.is_tree(
                strict=strict) and self.edges_covered() and self.is_connected() and self.edge_function_holds() and \
                self.inverse_edge_function_holds():
            return True
        else:
            logging.error('ERROR in Tree Decomposition.')
            return False

    def __str__(self):
        string = StringIO()
        self.write(string)
        return string.getvalue()
