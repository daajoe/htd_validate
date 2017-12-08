import logging
import traceback
from collections import Counter

import networkx as nx
from cStringIO import StringIO
from itertools import count, imap, chain, izip
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

    def __len__(self):
        return len(self.bags)

    @staticmethod
    def from_file(filename, strict=False):
        """
        :param strict: strictly enforce PACE requirements for the input format (pace specs are unnecessarily strict)
        :param filename:
        :rtype: TreeDecomposition
        :return:
        """
        td = TreeDecomposition()
        with open(filename, 'r') as fobj:
            num_bags = td_max_bag_size = num_vertices = 0
            try:
                header_seen = False
                edge_seen = False
                nr = 0
                for line in fobj.readlines():
                    line = line.split()
                    nr = nr + 1
                    # noinspection PySimplifyBooleanCheck
                    if line == []:
                        continue
                    if line[0] == 'c':
                        logging.info('-' * 20 + 'INFO from decomposition reader' + '-' * 20)
                        logging.info('%s' % ' '.join(line))
                        logging.info('-' * 80)
                        continue
                    elif line[0] == 's' and line[1] == 'td':
                        if header_seen:
                            logging.critical('L(%s). Duplicate header. Exiting...' % nr)
                            exit(2)
                        try:
                            num_bags, td_max_bag_size, num_vertices = map(int, line[2:])
                        except ValueError, e:
                            logging.error(e)
                            logging.critical('L(%s). Too many or too few arguments in header. Exiting...' % nr)
                            exit(2)
                        header_seen = True
                    elif line[0] == 'b':
                        if not header_seen:
                            logging.critical('L(%s). Bag before header. Exiting...' % nr)
                            exit(2)
                        if strict and edge_seen:
                            logging.error('L(%s). Edge before bag. Exiting...' % nr)
                            exit(2)
                        if len(line) < 2:
                            logging.critical('L(%s). Some bag has no index. Exiting...' % nr)
                            exit(1)
                        if strict and len(line) < 3:
                            logging.error('L(%s). Empty bag. Exiting...' % nr)
                            exit(2)
                        # if not strict and len(line) < 2:
                        #     continue
                        bag_name = int(line[1])
                        if td.bags.has_key(bag_name):
                            logging.critical('L(%s). Duplicate bag. Exiting...' % nr)
                            exit(2)
                        # TODO: implement type checking for htd|fhtd
                        td.bags[bag_name] = set(map(int, line[2:]))
                        td.tree.add_node(bag_name)
                    else:
                        if strict and not header_seen:
                            logging.error('L(%s). Edge before header. Exiting...' % nr)
                            exit(2)
                        u, v = map(int, line)
                        td.tree.add_edge(u, v)
                        edge_seen = True
            except ValueError as e:
                logging.critical("Undefined input.")
                logging.critical(e)
                logging.warning("Output was:")
                fobj.seek(0)
                for line in fobj.readlines():
                    logging.warning(line)
                for line in traceback.format_exc().split('\n'):
                    logging.critical(line)
                logging.critical('Exiting...')
                exit(143)
            # decomps of single bags require special treatment
            if len(td) == 1:
                # noinspection PyUnresolvedReferences
                td.tree.add_node(td.bags.iterkeys().next())
            if td.max_bag_size() != td_max_bag_size:
                logging.critical(
                    'Bag Size does not match the header was %s expected %s.\n' % (td.max_bag_size(), td_max_bag_size))
                exit(2)
            if len(td) != num_bags:
                logging.critical('Number of bags differ. Was %s expected %s.\n' % (len(td), num_bags))
                exit(2)
            if td.num_vertices > num_vertices:
                logging.critical(
                    'Number of vertices differ (>). Was %s expected %s.\n' % (td.num_vertices, num_vertices))
                exit(2)
            print strict
            if td.num_vertices < num_vertices and strict:
                logging.warning(
                    'Number of vertices differ (<). Was %s expected %s.\n' % (td.num_vertices, num_vertices))
                exit(2)
        return td

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

    @property
    def num_vertices(self):
        return len(set(chain.from_iterable(self.bags.itervalues())))
