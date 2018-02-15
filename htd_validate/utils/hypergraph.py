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
import gzip

from bz2 import BZ2File
from cStringIO import StringIO
from itertools import imap, izip

try:
    import backports.lzma as xz

    xz = True
except ImportError:
    xz = False

import mimetypes


class SymTab:
    def __init__(self, offset=0):
        self.__offset = offset
        self.name2id = {}
        self.id2name = {}

    def clear(self):
        self.name2id.clear()
        self.id2name.clear()

    def __getitem__(self, key):
        try:
            return self.name2id[key]
        except KeyError:
            val = self.__offset + len(self.name2id) + 1
            self.name2id[key] = val
            self.id2name[val] = key
            return val

    def get(self, key):
        return self.__getitem__(key)


class Hypergraph(object):
    __d = {}

    def __init__(self, non_numerical=False):
        self.__edges = dict()
        self.__vertices = set()
        self.__non_numerical = non_numerical
        if self.__non_numerical:
            self.__nsymtab = SymTab()
            self.__elabel = {}

    @property
    def adj(self):
        nbhs = dict()
        for k in self.__vertices:
            nbhs[k] = self.adj(k)
        return nbhs

    def adj(self, v):
        nbh = dict()
        for e in self.__edges.values():
            if v in e:
                for ex in e:
                    if ex != v:
                        nbh[ex] = Hypergraph.__d
        return nbh

    def __delitem__(self, v):
        del self.__vertices[v]
        for k in self.__edges:
            if v in self.__edges[k]:
                del self.__edges[k]

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
    def fromstream_dimacslike(clazz, stream):
        num_edges = 0
        num_verts = 0

        is_dimacs = False
        HG = clazz()
        for line in stream.readlines():
            line = line.split()
            if not line:
                continue
            elif line[0] == 'p':
                is_dimacs = line[1] == 'edge'
            elif line[0] != 'c':
                if is_dimacs:
                    HG.add_hyperedge(map(int, line[1:]))
                else:
                    HG.add_hyperedge(map(int, line))

        if HG.number_of_edges() < num_edges:
            print("edges missing: read=%s announced=%s" % (HG.number_of_edges(), num_edges))
        if HG.number_of_nodes() < num_verts:
            print("vertices missing: read=%s announced=%s" % (HG.number_of_edges(), num_edges))
        return HG

    # TODO: symtab

    @classmethod
    def fromstream_fischlformat(clazz, stream):
        HG = clazz(non_numerical=True)

        for line in stream:
            line = line[:-2]
            edge_name = None
            edge_vertices = []

            collect = []
            for char in line:
                if char == '(':
                    edge_name = ''.join(collect)
                    collect = []
                elif char == ',' or char == ')':
                    edge_vertices.append(''.join(collect))
                    collect = []
                elif char != ')':
                    collect.append(char)
            HG.add_hyperedge(edge_vertices, name=edge_name)
        return HG

    # TODO: move from_file to a central part

    @classmethod
    def from_file(clazz, filename, fischl_format=False):
        """
        :param filename: name of the file to read from
        :type filename: string
        :rtype: Graph
        :return: a list of edges and number of vertices
        """
        return clazz._from_file(filename, fischl_format=fischl_format)

    # TODO: check whether we need the header_only option
    @classmethod
    def _from_file(clazz, filename, header_only=False, fischl_format=False):
        """
        :param filename: name of the file to read from
        :type filename: string
        :param header_only: read header only
        :rtype: Graph
        :return: imported hypergraph
        """
        if header_only:
            raise NotImplemented
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
            if fischl_format:
                hypergraph = Hypergraph.fromstream_fischlformat(stream)
            else:
                hypergraph = Hypergraph.fromstream_dimacslike(stream)
        finally:
            if stream:
                stream.close()

        return hypergraph

    def clear(self):
        self.__vertices.clear()
        self.__edges.clear()
        if self.__non_numerical:
            self.__elabel.clear()
            self.__nsymtab.clear()

    def add_node(self, x):
        if self.__non_numerical:
            v = self.__nsymtab[x]
        else:
            v = x
        self.__vertices.add(v)
        return v

    def add_hyperedge(self, X, name=None):
        if self.__non_numerical:
            X = map(self.__nsymtab.get, X)
        edge_id = len(self.__edges) + 1

        if self.__non_numerical and name is not None:
            self.__elabel[edge_id] = name

        #remove/avoid already subsets of edges
        sx = set(X)
        for e in self.__edges.values():
            if sx.issubset(e):
                return None

        self.__edges[edge_id] = tuple(X)
        self.__vertices.update(X)
        return X

    def edge_iter(self):
        return self.__edges.iterkeys()

    def __iter__(self):
        return self.edge_iter()

    def __contains__(self, v):
        return v in self.__vertices

    def __len__(self):
        return len(self.__vertices)

    def num_hyperedges(self):
        return len(self.__edges)

    def get_nsymtab(self):
        return self.__nsymtab

    def write_dimacs(self, stream):
        return self.write_graph(stream, dimacs=True)

    def write_gr(self, stream):
        return self.write_graph(stream, dimacs=False)

    def write_graph(self, stream, dimacs=False):
        """
        :param stream: stream where to output the hypergraph
        :type stream: cString
        :param copy: return a copy of the original hypergraph
        :type copy: bool
        :param dimacs: write dimacs header (or gr header)
        :type dimacs: bool
        :rtype Graph, dict
        :return: written hypergraph, remapping of vertices from old hypergraph
        """
        gr_string = 'edge' if dimacs else 'htw'
        s = 'p ' if dimacs else ''
        stream.write('p %s %s %s\n' % (gr_string, self.number_of_nodes(), self.number_of_edges()))
        s = 'e ' if dimacs else ''
        for e_id, nodes in izip(xrange(self.number_of_edges()), self.edges_iter()):
            nodes = ' '.join(imap(str, nodes))
            stream.write('%s%s %s\n' % (s, e_id + 1, nodes))
        stream.flush()

    def __str__(self):
        string = StringIO()
        self.write_gr(string)
        return string.getvalue()

    def __repr__(self): return self.__str__()
