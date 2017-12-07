#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017
# Johannes K. Fichte, TU Wien, Austria*
#
# *) also affiliated with University of Potsdam(R) :P
# *) is not allowed to contain parts of nuts ;P
#
# hypergraph.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.  hypergraph.py is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public
# License along with hypergraph.py.  If not, see
# <http://www.gnu.org/licenses/>.
# from __future__ import print_function
from cStringIO import StringIO
import gzip
from bz2 import BZ2File
from itertools import count, izip

try:
    import backports.lzma as xz

    xz = True
except ImportError:
    xz = False

import mimetypes
import networkx as nx


class Hypergraph(object):
    def __init__(self, non_numerical=False):
        self.__edges = dict()
        self.__vertices = set()
        self.__non_numerical = non_numerical
        if self.__non_numerical:
            self.__tab = dict()
            self.__id_tab = dict()
            self.__node_label = dict()
            self.__edge_label = dict()

    def number_of_edges(self):
        return len(self.__edges)

    def number_of_nodes(self):
        return len(self.__vertices)

    def edges_iter(self):
        return iter(self.__edges.values())

    # TODO: copy?
    def edges(self):
        return self.__edges

    def get_edge(self, e):
        return self.__edges[e]

    def edge_ids_iter(self):
        return iter(self.__edges.keys())

    # TODO:
    def nodes_iter(self):
        return iter(self.__vertices)

    @classmethod
    def fromstream(clazz, stream):
        is_dimacs = False
        HG = clazz()
        for line in stream.readlines():
            line = line.split()
            if line == []:
                continue
            elif line[0] == 'p':
                is_dimacs = line[1] == 'edge'
            elif line[0] != 'c':
                if is_dimacs:
                    HG.add_hyperedge(map(int, line[1:]))
                else:
                    HG.add_hyperedge(map(int, line))
        return HG

    # TODO: move from_file to a central part

    @classmethod
    def from_file(clazz, filename):
        """
        :param filename: name of the file to read from
        :type filename: string
        :rtype: Graph
        :return: a list of edges and number of vertices
        """
        return clazz._from_file(filename)

    # TODO: check whether we need the header_only option
    @classmethod
    def _from_file(clazz, filename, header_only=False):
        """
        :param filename: name of the file to read from
        :type filename: string
        :param header_only: read header only
        :rtype: Graph
        :return: imported hypergraph
        """
        if header_only:
            raise NotImplemented
        num_edges = None
        num_verts = None
        is_dimacs = False
        stream = None
        hypergraph = clazz()
        try:
            mtype = mimetypes.guess_type(filename)[1]
            if mtype is None:
                stream = open(filename, 'r')
            elif mtype == 'bzip2':
                stream = BZ2File(filename, 'r')
            elif mtype == 'gz':
                stream = gzip.open(filename, 'r')
            elif mtype == 'xz' and xz:
                stream = xz.open(filename, 'r')
            else:
                raise IOError('Unknown input type "%s" for file "%s"' % (mtype, filename))

            hypergraph = Hypergraph.fromstream(stream)
        finally:
            if stream:
                stream.close()

        if hypergraph.number_of_edges() < num_edges:
            print("edges missing: read=%s announced=%s" % (hypergraph.number_of_edges(), num_edges))
        if hypergraph.number_of_nodes() < num_verts:
            print("vertices missing: read=%s announced=%s" % (hypergraph.number_of_edges(), num_edges))
        return hypergraph

    def add_node(self, x, **label):
        if self.__non_numerical:
            v = self.__vertex_id(x)
        if label:
            self.__node_label[v] = label
        self.__vertices.add(x)
        return v

    def add_hyperedge(self, X, label=None):
        if self.__non_numerical:
            X = map(self.__vertex_id, X)
        if label:
            self.__edge_label[X] = label

        self.__edges[len(self.__edges) + 1] = tuple(X)
        self.__vertices.update(X)
        return X

    # def __vertex_id(self, x):
    #     if self.__tab.has_key(x):
    #         return self.__tab[x]
    #     else:
    #         self.__tab[x] = len(self.__tab) + 1
    #         self.__id_tab[self.__tab[x]] = x
    #         return self.__tab[x]

    def edge_iter(self):
        return self.__edges.iterkeys()

    def __iter__(self):
        return self.edge_iter()

    def num_hyperedges(self):
        return len(self.__edges)

    def num_vertices(self):
        return len(self.__tab)

    def get_symtab(self):
        return self.__tab

    # def get_edge_labels(self):
    #     return self.__edge_label

    # def get_node_labels(self):
    #     return self.__node_label

    # def get_node_name(self, x):
    #     return self.__id_tab[x]

    # def __getitem__(self, x):
    #     if isinstance(x, tuple):
    #         return self.get_edge_labels()[x]
    #     else:
    #         return self.get_node_labels()[x]
