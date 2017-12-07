import logging
from collections import defaultdict

import networkx as nx
from cStringIO import StringIO


# python: check abstract class
class Decomposition(object):
    def __init__(self):
        self.tree = nx.DiGraph()
        self.bags = {}
        self.hypergraph = None

    @staticmethod
    def graph_type():
        raise NotImplementedError(
            "abstract method -- subclass %s must override" % self.__class__)

    def edges_covered(self):
        # initialise with edges
        covered_edges = {e: False for e in self.hypergraph.edges_iter()}
        for e in self.hypergraph.edges_iter():
            if not any(set(e) <= bag for bag in self.bags.itervalues()):
                logging.error('Edge "%s" is not covered in any bag.' % str(e))
                return False
        return True

    def bag_occuences(self):
        vertex2bags = defaultdict(set)
        for n, bag in self.bags.iteritems():
            for v in bag:
                vertex2bags[v].add(n)
        logging.info('Bag occurences yields: %s' % vertex2bags)
        return vertex2bags

    def is_connected(self):
        vertex2bags = self.bag_occuences()
        for v in self.hypergraph.nodes_iter():
            SG = self.tree.subgraph(vertex2bags[v])
            if not nx.is_connected(SG.to_undirected()):
                logging.error('Subgraph induced by vertex "%s" is not connected' % v)
                string = StringIO()
                nx.write_multiline_adjlist(SG, string)
                logging.error('Involved bags: %s' % vertex2bags[v])
                logging.error('Nodes of the hypergraph (should be the same): %s' % SG.nodes())
                logging.error('Begin Adjacency Matrix')
                # we skip comments from networkx
                for line in string.getvalue().split('\n')[3:-1]:
                    logging.error('%s' % line)
                logging.error('End Adjacency Matrix')
                return False
        return True
