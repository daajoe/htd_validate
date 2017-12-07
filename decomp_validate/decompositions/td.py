import logging
import subprocess
import sys
from tempfile import NamedTemporaryFile

import networkx as nx
from cStringIO import StringIO
from itertools import count, imap, chain, izip
from networkx.drawing.nx_agraph import graphviz_layout
from operator import itemgetter

from decomp_validate.decompositions import Decomposition
from decomp_validate.utils import Graph


class TreeDecomposition(Decomposition):
    @staticmethod
    def graph_type():
        return Graph.__name__

    def __init__(self, plot_if_td_invalid=False):
        Decomposition.__init__(self)

    def __len__(self):
        return len(self.bags)

    @staticmethod
    def from_file(filename, enforceStrict=False):
        """
        :param filename:
        :rtype: TreeDecomposition
        :return:
        """
        td = TreeDecomposition()
        with open(filename, 'r') as fobj:
            num_bags = td_max_bag_size = num_vertices = 0
            try:
                for line in fobj.readlines():
                    line = line.split()
                    # noinspection PySimplifyBooleanCheck
                    if line == []:
                        continue
                    if line[0] == 'c':
                        logging.warning('-' * 20 + 'INFO from decomposition reader' + '-' * 20)
                        logging.warning('%s' % ' '.join(line))
                        logging.warning('-' * 80)
                        continue
                    elif line[0] == 's' and line[1] == 'td':
                        num_bags, td_max_bag_size, num_vertices = map(int, line[2:])
                    elif line[0] == 'b':
                        if enforceStrict and len(line) < 2: return TreeDecomposition()
                        bag_name = int(line[1])
                        td.bags[bag_name] = set(map(int, line[2:]))
                        td.tree.add_node(bag_name)
                    else:
                        u, v = map(int, line)
                        td.tree.add_edge(u, v)
            except ValueError as e:
                logging.critical("Undefined input.")
                logging.critical(e)
                logging.warning("Output was:")
                for line in lines.split('\n'):
                    logging.warning(line)
                for line in traceback.format_exc().split('\n'):
                    logging.critical(line)
                logging.critical('Exiting...')
                exit(143)
            # decomps of single bags require special treatment
            if len(td) == 1:
                # noinspection PyUnresolvedReferences
                td.tree.add_node(td.bags.iterkeys().next())
            if len(td) != num_bags:
                sys.stderr.write('WARNING: Number of bags differ. Was %s expected %s.\n' % (len(td), num_bags))
                if enforceStrict: return TreeDecomposition()
            if len(set(chain.from_iterable(td.bags.itervalues()))) != num_vertices:
                sys.stderr.write(
                    'WARNING: Number of vertices differ. Was %s expected %s.\n' % (
                        td.tree.number_of_nodes(), num_vertices))
                if enforceStrict: return TreeDecomposition()
            if td.max_bag_size() != td_max_bag_size:
                sys.stderr.write(
                    'WARNING: Number of vertices differ. Was %s expected %s.\n' % (
                        td.max_bag_size(), td_max_bag_size))
                if enforceStrict: return TreeDecomposition()
        return td

    #TODO: move the validation parts to the validators???
    def vertices_covered(self):
        occurences = self.bag_occuences()
        for v in self.hypergraph.nodes_iter():
            if v not in occurences:
                logging.error('Vertex "%v" does not occur in any bag.' %v)
                logging.error('Bags contain the following vertices: %s' %occurences)
                return False
        return True

    def validate(self, graph):
        self.hypergraph = graph
        if self.edges_covered() and self.is_connected() and self.vertices_covered():
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

    def relabeled_decomposition(self, offset, vertex_mapping, inplace=False):
        if inplace:
            raise NotImplementedError("Not implemented yet.")
        offset += 1
        tree_mapping = {org_id: id for id, org_id in izip(count(start=offset), self.tree.nodes_iter())}
        new_bags = {}
        for i in xrange(offset, offset + len(self.tree.nodes())):
            new_bags[i] = self.bags[self.tree.nodes()[i - offset]]
        ret_tree = nx.relabel_nodes(self.tree, tree_mapping, copy=False)
        # relabeled_decomposition the contents of the bags according to mapping
        inv_mapping = dict(imap(reversed, vertex_mapping.items()))
        for key, bag in new_bags.iteritems():
            new_bags[key] = set(map(lambda x: inv_mapping[x], bag))
        # TODO: refactor
        return TreeDecomposition(tree=ret_tree, bags=new_bags, temp_path=self.temp_path, delete_temp=self.delete_temp,
                                 plot_if_td_invalid=self.plot_if_td_invalid)

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

    def simplify(self):
        node = iter(self.tree.nodes())
        while True:
            try:
                i = next(node)
                neigh_list = set(self.tree[i])
                for neigh in self.tree[i]:
                    if self.bags[i].issubset(self.bags[neigh]):
                        for neigh1 in neigh_list - set([neigh]):
                            self.tree.add_edge(neigh, neigh1)
                        self.tree.remove_node(i)
                        del self.bags[i]
                        break
            except StopIteration:
                break
        if self.always_validate:
            self.validate2()


class TrivialTreeDecomposition(TreeDecomposition):
    def __init__(self):
        super(TrivialTreeDecomposition, self).__init__()

    def from_graph(self, graph):
        self.bags = {1: graph.nodes()}
        self.tree.add_node(1)
