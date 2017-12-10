import logging

import networkx as nx
from cStringIO import StringIO
from itertools import count, imap, izip
from networkx.drawing.nx_agraph import graphviz_layout
from operator import itemgetter

from htd_validate.decompositions import Decomposition
from htd_validate.utils import Graph


class TreeDecomposition(Decomposition):
    _problem_string = 'td'

    @classmethod
    def graph_type(cls):
        return Graph.__name__

    def __init__(self, plot_if_td_invalid=False):
        Decomposition.__init__(self)

    @staticmethod
    def _read_header(line):
        ret = {'max_bag_size': int(line[3])}
        if len(line) > 5:
            logging.critical('Header contained too many parameters. Exiting...')
            exit(2)
        return ret

    @staticmethod
    def _reader(line):
        pass

    @staticmethod
    def specific_valiation(td, problem_statement):
        if td.max_bag_size() != problem_statement['max_bag_size']:
            logging.critical(
                'Bag Size does not match the header was %s expected %s.\n' % (
                    td.max_bag_size(), problem_statement['max_bag_size']))
            exit(2)

    # TODO: move the validation parts to the validators???
    def vertices_covered(self):
        occurences = self.bag_occuences()
        for v in self.hypergraph.nodes_iter():
            if v not in occurences:
                logging.error('Vertex "%s" does not occur in any bag.' % v)
                logging.error('Bags contain the following vertices: %s' % occurences)
                return False
        return True

    def validate(self, graph):
        self.hypergraph = graph
        if self.is_tree() and self.edges_covered() and self.is_connected() and self.vertices_covered():
            return True
        else:
            logging.error('ERROR in Tree Decomposition.')
            return False

    def write(self, ostream):
        tree_mapping = {org_id: id for id, org_id in izip(count(start=1), self.tree.nodes_iter())}
        tree = nx.relabel_nodes(self.tree, tree_mapping, copy=True)
        max_bag_size = self.max_bag_size()  # reduce(max, map(len, self.bags.itervalues() or [0]))
        num_vertices = reduce(lambda x, y: max(x, max(y or [0])), self.bags.itervalues(), 0)
        ostream.write('s td %s %s %s\n' % (len(self.bags), max_bag_size, num_vertices))

        relabeled_bags = {tree_mapping[k]: v for k, v in self.bags.iteritems()}
        relabeled_bags = sorted(relabeled_bags.items(), key=itemgetter(0))
        for bag_id, bag in relabeled_bags:
            ostream.write('b %s %s\n' % (bag_id, ' '.join(imap(str, bag))))
        for u, v in tree.edges_iter():
            ostream.write('%s %s\n' % (u, v))
        ostream.flush()

    def __str__(self):
        string = StringIO()
        self.write(string)
        return string.getvalue()

    def max_bag_size(self):
        ret = 0
        for b in self.bags.itervalues():
            ret = max(ret, len(b))
        return ret

    def get_first_node(self, max_bag_size):
        bagids2lengths = dict(zip(self.bags.keys(), map(len, self.bags.values())))
        lengths = bagids2lengths.values()
        if not max_bag_size:
            max_bag_size = max(lengths)
        root_id = lengths.index(max_bag_size)
        return bagids2lengths.keys()[root_id]

    def show(self, layout, nolabel=0):
        """ show hypergraph
        layout 1:graphviz,
        2:circular,
        3:spring,
        4:spectral,
        5: random,
        6: shell
        """
        if not self.plot_if_td_invalid:
            logging.error('written_decomp(tree)=%s', self.tree.edges())
            logging.error('written_decomp(bags)=%s', self.bags)

            return
        else:
            import matplotlib.pyplot as plt
            import matplotlib

            matplotlib.use('TkAgg')

            m = self.tree.copy()
            pos = graphviz_layout(m)
            if layout == 1:
                pos = graphviz_layout(m)
            elif layout == 2:
                pos = nx.circular_layout(m)
            elif layout == 3:
                pos = nx.spring_layout(m)
            elif layout == 4:
                pos = nx.spectral_layout(m)
            elif layout == 5:
                pos = nx.random_layout(m)
            elif layout == 6:
                pos = nx.shell_layout(m)
            if not nolabel:
                nx.draw_networkx_edge_labels(m, pos)
            nx.draw_networkx_nodes(m, pos)
            if self.bags:
                bags = {k: '%s:%s' % (k, str(sorted(list(v)))) for k, v in self.bags.iteritems()}
                nx.draw_networkx_labels(m, pos, bags)
            else:
                nx.draw_networkx_labels(m, pos)
            nx.draw(m, pos)
            plt.show()
