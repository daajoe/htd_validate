import logging
import os
import traceback
from collections import defaultdict

import networkx as nx
from cStringIO import StringIO
from itertools import chain


class Decomposition(object):
    _problem_string = 'missing'
    _data_type = int

    def __new__(cls, *args, **kwargs):
        if cls is Decomposition:
            raise TypeError("base class may not be instantiated")
        return object.__new__(cls, *args, **kwargs)

    def __init__(self):
        self.tree = nx.DiGraph()
        self.bags = {}
        self.hypergraph = None

    @staticmethod
    def graph_type():
        raise NotImplementedError("abstract method -- subclass must override")

    def __len__(self):
        return len(self.bags)

    @classmethod
    def from_file(cls, filename, strict=False):
        """
        :param strict: strictly enforce PACE requirements for the input format (pace specs are unnecessarily strict)
        :param filename:
        :rtype: TreeDecomposition
        :return:
        """
        header_seen = False
        nr = 0

        def log_critical(string):
            logging.critical('%s:L(%s). %s  Exiting...' % (os.path.basename(filename), nr, string))

        decomp = cls()
        with open(filename, 'r') as fobj:
            num_bags = num_vertices = 0
            header = {}
            try:
                edge_seen = False
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
                    elif line[0] == 's' and line[1] == cls._problem_string:
                        if header_seen:
                            log_critical('Duplicate header.')
                            exit(2)
                        try:
                            header['num_bags'] = int(line[2])
                            header['num_vertices'] = int(line[4])
                            header.update(cls._read_header(line))
                        except ValueError as e:
                            logging.error(e)
                            log_critical('Too many or too few arguments in header.')
                            exit(2)
                        header_seen = True
                    elif line[0] == 'b':
                        if not header_seen:
                            log_critical('Bag before header.')
                            exit(2)
                        if strict and edge_seen:
                            log_critical('Edge before bag.')
                            exit(2)
                        if len(line) < 2:
                            log_critical('Some bag has no index.')
                            exit(1)
                        if strict and len(line) < 3:
                            log_critical('Empty bag.')
                            exit(2)
                        bag_name = int(line[1])
                        if decomp.bags.has_key(bag_name):
                            log_critical('Duplicate bag.')
                            exit(2)
                        # TODO: implement type checking for htd|fhtd
                        # TODO: BUT NOT HERE! type checking required in 'w' line ~> _reader
                        try:
                            decomp.bags[bag_name] = set(map(int, line[2:]))
                        except ValueError as e:
                            log_critical("Type checking failed (expected %s)." % int) #cls._data_type)
                            logging.critical("Full exception %s." % e)
                            exit(2)
                        decomp.tree.add_node(bag_name)
                    else:
                        if cls._reader(decomp, line):
                            continue
                        else:
                            if strict and not header_seen:
                                log_critical('Edge before header.')
                                exit(2)
                            u, v = map(int, line)
                            if u > header['num_bags']:
                                log_critical("Edge label %s out of bounds (expected max %s bags)." %(u,num_bags))
                                exit(2)
                            if v > header['num_bags']:
                                log_critical("Edge label %s out of bounds (expected max %s bags)." %(v,num_bags))
                                exit(2)
                            if u not in decomp.bags.keys():
                                log_critical(
                                    "Edge in the tree (%s,%s) without a corresponding bag for node %s." % (u, v, u))
                                exit(2)
                            if v not in decomp.bags.keys():
                                log_critical(
                                    "Edge in the tree (%s,%s) without a corresponding bag for node %s." % (u, v, v))
                                exit(2)
                            decomp.tree.add_edge(u, v)
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
            if not header_seen:
                logging.critical('Missing header. Exiting...')
                exit(2)
            if len(decomp) == 1:
                # noinspection PyUnresolvedReferences
                decomp.tree.add_node(decomp.bags.iterkeys().next())
            if decomp.specific_valiation(decomp, header):
                logging.critical('Decomposition specific validation failed.')
                exit(2)
            if len(decomp) != header['num_bags']:
                logging.critical('Number of bags differ. Was %s expected %s.\n' % (len(decomp), header['num_bags']))
                exit(2)
            if decomp.num_vertices > header['num_vertices']:
                logging.critical(
                    'Number of vertices differ (>). Was %s expected %s.\n' % (decomp.num_vertices, header['num_vertices']))
                exit(2)
            if decomp.num_vertices < header['num_vertices'] and strict:
                logging.warning(
                    'Number of vertices differ (<). Was %s expected %s.\n' % (decomp.num_vertices, num_vertices))
                exit(2)
        return decomp

    def edges_covered(self):
        # initialise with edges
        # TODO: something missing here
        covered_edges = {e: False for e in self.hypergraph.edges_iter()}
        for e in self.hypergraph.edges_iter():
            if not any(set(e) <= bag for bag in self.bags.itervalues()):
                logging.error('Edge "%s" is not covered in any bag.' % str(e))
                return False
        return True

    def is_tree(self):
        ret = len(self.tree) == 0 or nx.is_tree(self.tree)
        if not ret:
            logging.error('The underlying graph is not a tree.')
        return ret

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

    @property
    def num_vertices(self):
        return len(set(chain.from_iterable(self.bags.itervalues())))

    @staticmethod
    def specific_valiation(td, problem_statement):
        raise NotImplementedError("abstract method -- subclass must override")

    @staticmethod
    def _reader(decomp, line):
        raise NotImplementedError("abstract method -- subclass must override")

    @staticmethod
    def _read_header(line):
        raise NotImplementedError("abstract method -- subclass must override")
