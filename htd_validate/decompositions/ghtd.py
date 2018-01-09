import logging
from collections import defaultdict

import networkx as nx
from cStringIO import StringIO
from itertools import count, imap, izip
from operator import itemgetter

from htd_validate.decompositions import Decomposition
from htd_validate.utils import Hypergraph


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

    @classmethod
    def _read_header(cls, line):
        if len(line) < 6:
            logging.critical('Header contained too little parameters. Exiting...')
            exit(2)

        ret = {'max_function_value': cls._data_type(line[3]),
               'num_vertices': int(line[4]),
               'num_hyperedges': int(line[5])}

        if len(line) > 6:
            logging.critical('Header contained too many parameters. Exiting...')
            exit(2)
        return ret

    @classmethod
    def _reader(cls, decomp, line):
        if line[0] == 'w':
            decomp.hyperedge_function[int(line[1])][int(line[2])] = cls._data_type(line[3])
            return True
        return False

    @staticmethod
    def specific_valiation(decomp, header):
        if len(decomp.hyperedge_function) != header['num_bags']:
            logging.error(
                'Too many mappings. Found %s expected %s \n' % (
                len(decomp.hyperedge_function), header['num_bags']))
            exit(2)
        for b in decomp.bags.iterkeys():
            for e in xrange(1, header['num_hyperedges']+1):
                if not decomp.hyperedge_function[b].has_key(e):
                    logging.error(
                        'Missing function mapping for node %s of the tree. Missing for edge %s \n' % (b, e))
                    exit(2)
        if header['max_function_value'] != decomp.width():
            logging.error(
                'Given width is wrong. Computed width %s, given width %s \n' % (decomp.width(), header['max_function_value']))
            exit(2)

    # TODO: detect format from file header
    # TODO: syntax check for htd|ghtd|fhtd
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
        weight = [0]    #special case for the empty graph
        for t in self.tree.nodes_iter():
            weight.append(sum(self.hyperedge_function[t].itervalues()))
        logging.info("Width is '%s'." % max(weight))
        return max(weight)

    @property
    def problem_string(self):
        return self._problem_string
