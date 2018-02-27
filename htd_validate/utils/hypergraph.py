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

try:
    import cplex as cx
except ImportError:
    cx = None

try:
    import clingo
except:
    clingo = None

from pymonad.Reader import curry

from UserString import MutableString
import subprocess
import sys
import io

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
    #__edge_type = type(tuple)
    __edge_type = tuple

    def __init__(self, non_numerical=False, vertices=None):
        self.__edges = dict()
        if vertices is None:
            vertices = set()
        self.__vertices = vertices
        self.__non_numerical = non_numerical
        if self.__non_numerical:
            self.__nsymtab = SymTab()
            self.__elabel = {}

    def edge_rank(self, n):
        return map(lambda x: tuple(x, len(x)), self.adjByNode(n))

    #--solve-limit=<n>[,<m>] : Stop search after <n> conflicts or <m> restarts
    def largest_clique_asp(self, solve_limit="umax,umax", enum=True, usc=True):
        if clingo is None:
            raise ImportError()

        @curry
        def __on_model(aset, model):
            aset[1] |= model.optimality_proven
            if model.cost[0] <= aset[0]:
                if model.cost[0] < aset[0]:
                    aset[2] = []
                aset[0] = model.cost[0]
                aset[2].append(str(model).split(" "))

        aset = [sys.maxint, False, []]
        c = clingo.Control()

        prog = MutableString()

        for u in self.__vertices:
            prog += " {{ u{0} }}. ".format(u)
            prog += " #show u{0}/0. ".format(u)
            prog += " :~ not u{0}.[1,u{1}] ".format(u,u)

        adj = self.adj

        for u in self.__vertices:
            for v in self.__vertices:
                if u < v and v not in adj[u]:
                    prog += " :- u{0}, u{1}. ".format(u, v)

        constr = set()
        for e in self.__edges.values():
            #prevent 3 elements from the same edge
            k = 3
            sub = range(0, k)
            while True: #sub[0] <= len(e) - k:
                rule = " :- "
                pos = 0
                for v in sub:
                    rule += " u{0}{1}".format(e[v], ". " if pos == k - 1 else ",")
                    pos += 1

                if rule not in constr:
                    constr.add(rule)
                    prog += rule

                if sub[0] == len(e) - k:
                    break

                #next position
                for i in xrange(k - 1, -1, -1):
                    if sub[i] < len(e) - (k - i - 1):
                        sub[i] += 1
                        for j in xrange(i + 1, k):
                            sub[j] = sub[i] + (j - i)

        if usc:
            c.configuration.solver.opt_strategy = "usc,pmres,disjoint,stratify"
            c.configuration.solver.opt_usc_shrink = "min"
        if enum:
            c.configuration.solve.opt_mode = "optN"
            c.configuration.solve.models = 0
        c.configuration.solve.solve_limit = solve_limit
        #print str(prog)
        c.add("prog", [], str(prog))
        c.ground([("prog", [])])

        c.solve(on_model=__on_model(aset))

        print len(aset[2]), aset


    def fractional_cover(self, verts):
        if cx is None:
            raise ImportError()

        problem = cx.Cplex()
        problem.objective.set_sense(problem.objective.sense.minimize)

        names = ["e{0}".format(e) for e in self.edges()]
        # coefficients
        problem.variables.add(obj=[1] * len(self.edges()),
                              lb=[0] * len(self.edges()),
                              # ub=upper_bounds,
                              names=names)

        # constraints
        constraints = []
        for k in verts:
            constraint = []
            for e in self.incident_edges(k):
                constraint.append("e{0}".format(e))
            if len(constraint) > 0:
                constraints.append([constraint, [1] * len(constraint)])

        problem.linear_constraints.add(lin_expr=constraints,
                                       senses=["G"] * len(constraints),
                                       rhs=[1] * len(constraints))#,
                                       #names=["c{0}".format(x) for x in names])

        problem.solve()
        assert(problem.solution.get_status() == 1)
        return problem.solution.get_objective_value()
        # print problem.solution.get_values()

    # @staticmethod
    # def project_edge(e, p):
    #    return [x for x in e if x not in p]

    def induce_edges(self, es):
        for e in es:
            self.add_hyperedge([x for x in e if x in self.__vertices])

    #can also contract edge parts >= 2, e[0] is the edge that is kept
    def contract_edge(self, e):
        assert(len(e) >= 2)
        dl = -1
        for (k, v) in self.__edges.iteritems():
            contr = [x for x in v if x not in e]
            #assert(len(contr) >= 1)
            if len(contr) == 0: # and contr[0] == e[0]:
                dl = k
            elif (len(contr) + 1 < len(v)) or (len(contr) + 1 == len(v) and e[0] not in v):
                contr.append(e[0])
                self.__edges[k] = Hypergraph.__edge_type(contr)
        if dl >= 0:
            del self.__edges[dl]
        self.__vertices.difference_update(e[1:])

    def incident_edges(self, v):
        edges = {}
        for (e, ge) in self.__edges.iteritems():
            if v in ge:
                edges[e] = ge
        return edges

    def edge_rank(self, n):
        #print self.incident_edges(n).values()
        return map(lambda x: (x, len(x)), self.incident_edges(n).values())

    # @staticmethod
    # def project_edge(e, p):
    #    return [x for x in e if x not in p]

    #def inc(self,v):
    #    nbh = dict()
    #    for e in self.__edges.values():
    #        if v in e:
    #            nbh[e] = Hypergraph.__d
    #    return nbh

    def adjByNode(self, v):
        nbh = dict()
        for e in self.__edges.values():
            if v in e:
                for ex in e:
                    if ex != v:
                        nbh[ex] = Hypergraph.__d
        return nbh

    @property
    def adj(self):
        nbhs = dict()
        for k in self.__vertices:
            nbhs[k] = self.adjByNode(k)
        return nbhs

    def __delitem__(self, v):
        #please do not make me copy everything :(
        #assert(Hypergraph.__edge_type == type(list))
        self.__vertices.remove(v)
        #del self.__vertices[v]
        dl = []
        for k, e in self.__edges.iteritems():
            if v in self.__edges[k]:
                #thank you, tuple!
                #del self.__edges[k][v]
                e = set(e)
                e.remove(v)
                self.__edges[k] = Hypergraph.__edge_type(e)
                #print self.__edges[k]
                dl.append((k, e))
        for k, e in dl:
            if len(e) <= 1 or self.isSubsumed(e, modulo=k):
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
            line = line.replace('\n', '')[:-1]
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
        if len(X) <= 1:
            return
        if self.__non_numerical:
            X = map(self.__nsymtab.get, X)
        edge_id = len(self.__edges) + 1

        if self.__non_numerical and name is not None:
            self.__elabel[edge_id] = name

        # remove/avoid already subsets of edges
        if not self.isSubsumed(set(X), checkSubsumes=True):
            self.__edges[edge_id] = Hypergraph.__edge_type(X)
            self.__vertices.update(X)
        return X

    def isSubsumed(self, sx, checkSubsumes=False, modulo=-1):
        for k, e in self.__edges.iteritems():
            if k == modulo:
                continue
            elif sx.issubset(e):
                return True
            elif checkSubsumes and sx.issuperset(e):  #reset the edge
                #print sx, e
                #self.__edges[k][:] = sx
                self.__edges[k] = Hypergraph.__edge_type(sx)
                return True
        return False

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

    def __repr__(self):
        return self.__str__()
