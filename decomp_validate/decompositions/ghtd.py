import logging
import traceback
from collections import defaultdict

import networkx as nx
from cStringIO import StringIO
from itertools import count, imap, chain, izip
from operator import itemgetter

from decomp_validate.decompositions import Decomposition
from decomp_validate.utils import Hypergraph


class GeneralizedHypertreeDecomposition(Decomposition):
    _problem_string = 'ghtd'

    @staticmethod
    def graph_type():
        return Hypergraph.__name__

    def __init__(self, plot_if_td_invalid=False):
        Decomposition.__init__(self)
        self.hypergraph = Hypergraph()
        self.hyperedge_function = defaultdict(dict)

    def __len__(self):
        return len(self.bags)

    # TODO: detect format from file header
    @classmethod
    def from_file(cls, filename, enforceStrict=False):
        """
        :param filename:
        :rtype: TreeDecomposition
        :return:
        """
        decomp = cls()
        with open(filename, 'r') as fobj:
            num_bags = max_function_value = num_vertices = 0
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
                    elif line[0] == 's' and line[1] == cls._problem_string:
                        num_bags, max_function_value, num_vertices, num_hyperedges = map(int, line[2:])
                    elif line[0] == 'b':
                        bag_name = int(line[1])
                        decomp.bags[bag_name] = set(map(int, line[2:]))
                        decomp.tree.add_node(bag_name)
                    elif line[0] == 'w':
                        decomp.hyperedge_function[int(line[1])][int(line[2])] = int(line[3])
                    else:
                        u, v = map(int, line)
                        if u not in decomp.bags.keys():
                            logging.error(
                                "ERROR (reading decomposition): Edge in the tree (%s,%s) without a corresponding bag for node %s." % (
                                    u, v, u))
                        if v not in decomp.bags.keys():
                            logging.error(
                                "ERROR (reading decomposition): Edge in the tree (%s,%s) without a corresponding bag for node %s." % (
                                    u, v, v))
                        decomp.tree.add_edge(u, v)
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
            if len(decomp) == 1:
                # noinspection PyUnresolvedReferences
                decomp.tree.add_node(decomp.bags.iterkeys().next())
            if len(decomp.hyperedge_function) != num_bags:
                logging.error(
                    'ERROR (reading decomposition): Missing function mapping for some node of the tree. '
                    'Was %s expected %s \n' % (
                        len(decomp.hyperedge_function), num_bags))
            if len(decomp) != num_bags:
                logging.error('ERROR (reading decomposition): Number of bags differ. Was %s expected %s.\n' % (
                    len(decomp), num_bags))
            if len(set(chain.from_iterable(decomp.bags.itervalues()))) != num_vertices:
                logging.error(
                    'ERROR (reading decomposition): Number of vertices differ. Was %s expected %s.\n' % (
                        decomp.tree.number_of_nodes(), num_vertices))
            if decomp.width() != max_function_value:
                logging.error(
                    'ERROR (reading decomposition): Bag size differs. Was %s expected %s.\n' % (
                        decomp.width(), max_function_value))
        return decomp

    @staticmethod
    def restricted_mapping(mydict, keys):
        return dict((k, mydict[k]) for k in keys if k in mydict)

    def _edge_ids_where_v_occurs(self, v):
        # {k: v for k, v in d.items() if v > 0}
        logging.debug("Computing hyperedges where v='%s' occurs..." % v)
        logging.debug("Hyperedges %s" % self.hypergraph.edges())
        edge_ids = filter(lambda e: v in self.hypergraph.get_edge(e), self.hypergraph.edge_ids_iter())
        logging.debug("Edge_ids are %s" % edge_ids)
        return edge_ids

    def _B(self, t):
        logging.info("Computing bag condition B(lambda_t) for node %s" % t)
        ret = set()
        # {v \in V(H) : (sum_{e \in E(H), v \in e} lambda_u(e)) \geq 1 } =>
        # {v : v \in V(H), (sum{lambda_u(e) : e \in E(H), v \in e}) \geq 1 }
        for v in self.hypergraph.nodes_iter():
            logging.info('v = %s' % v)
            # e \in E(H), v \in e: self._edge_ids_where_v_occurs(v)
            # lambda_u_e_v: {lambda_u(e) : e \in E(H), v \in e}
            lambda_u_e_v = map(lambda e: self.hyperedge_function[t][e], self._edge_ids_where_v_occurs(v))
            logging.info('lambda(%s) = %s' % (t, lambda_u_e_v))
            logging.info('sum(%s) = %s' % (t, sum(lambda_u_e_v)))
            if sum(lambda_u_e_v) >= 1:
                ret.add(v)
        logging.info("B(lambda_%s) = '%s'" % (t, ret))
        return ret

    def edge_function_holds(self):
        for t in self.tree.nodes_iter():
            if not (self.bags[t] <= self._B(t)):
                logging.error('Edge function property does not hold for node "%s"' % t)
                logging.error(
                    'Bag contains: "%s" while vertices from edge functions were "%s"' % (self.bags[t], self._B(t)))
                return False
        return True

    def validate(self, graph):
        self.hypergraph = graph
        if self.is_tree() and self.edges_covered() and self.is_connected() and self.edge_function_holds():
            return True
        else:
            logging.error('ERROR in Tree Decomposition.')
            return False

    def write(self, ostream):
        tree_mapping = {org_id: id for id, org_id in izip(count(start=1), self.tree.nodes_iter())}
        tree = nx.relabel_nodes(self.tree, tree_mapping, copy=True)
        num_vertices = reduce(lambda x, y: max(x, max(y or [0])), self.bags.itervalues(), 0)
        num_hyperedges = len(self.hypergraph.edges())
        ostream.write(
            's %s %s %s %s %s\n' % (self._problem_string, len(self.bags), self.width(), num_vertices, num_hyperedges))

        relabeled_bags = {tree_mapping[k]: v for k, v in self.bags.iteritems()}
        relabeled_bags = sorted(relabeled_bags.items(), key=itemgetter(0))
        for bag_id, bag in relabeled_bags:
            ostream.write('b %s %s\n' % (bag_id, ' '.join(imap(str, bag))))
        for u, v in tree.edges_iter():
            ostream.write('%s %s\n' % (u, v))
        ostream.flush()

        for t in self.bags.iterkeys():
            for e in self.hyperedge_function:
                ostream.write('w %s %s %s\n' % (t, e, self.hyperedge_function[t][e]))
        ostream.flush()

    def __str__(self):
        string = StringIO()
        self.write(string)
        return string.getvalue()

    def width(self):
        weight = []
        for t in self.tree.nodes_iter():
            weight.append(sum(self.hyperedge_function[t].itervalues()))
        logging.info("Width is '%s'." % max(weight))
        return max(weight)
