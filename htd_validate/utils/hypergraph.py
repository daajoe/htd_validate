#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017
# Johannes K. Fichte, TU Wien, Austria*
# Markus A. Hecher, TU Wien, Austria*
#
# Copyright 2019, 2020
# Johannes K. Fichte, TU Dresden, Germany*
# Markus A. Hecher, TU Wien, Austria*
#
# *) also affiliated with University of Potsdam(R) :P
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
from __future__ import absolute_import

import copy
import gzip
import logging
import lzma
import mimetypes
import sys
import threading
import time
from bz2 import BZ2File
# noinspection PyUnresolvedReferences
from htd_validate.utils import relabelling as relab
from io import StringIO
import re

try:
    import cplex as cx
except ImportError:
    cx = None

# TODO solver handling
try:
    import z3
except ImportError:
    z3 = None

try:
    import clingo
except:
    clingo = None

# noinspection PyUnresolvedReferences
from htd_validate.utils.integer import safe_int


class SymTab:
    def __init__(self, offset=0):
        self.__offset = offset
        self.name2id = {}
        self.id2name = {}

    def clear(self):
        self.name2id.clear()
        self.id2name.clear()

    @property
    def n2id(self):
        return self.name2id

    @property
    def id2n(self):
        return self.id2name

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
    # __edge_type = type(tuple)
    __edge_type = tuple

    ACCURACY = 0.0000001

    def __init__(self, non_numerical=False, vertices=None):
        self.__edges = dict()
        if vertices is None:
            vertices = set()
        self.__vertices = vertices
        self.__non_numerical = non_numerical
        if self.__non_numerical:
            self.__nsymtab = SymTab()
            self.__elabel = {}

    # def edge_rank(self, n):
    #    return map(lambda x: tuple(x, len(x)), self.adjByNode(n))

    def edge_into(self, vertices, globalgraph):
        vertices = set(vertices)
        inters = vertices.intersection(self.__vertices)
        if len(inters) > 0:
            assert (len(inters) == 1)
            return inters, -1
        else:
            for k, v in globalgraph.__edges.items():
                inters = vertices.intersection(v).intersection(self.__vertices)
                if len(inters) >= 2:
                    assert (len(inters) == 2)
                    return inters, k
        return None, -1

    def iter_twin_neighbours(self):
        ngb = {}
        # TODO: fixme here seems to be something off
        for v in self.nodes_iter():
            tp = tuple(sorted(self.adjByNode(v, strict=False).keys()))
            if tp not in ngb:
                ngb[tp] = []
            ngb[tp].append(v)

        for v in ngb.values():
            assert (len(v) >= 1)
            if len(v) >= 2:
                yield v

    def iter_twin_vertices(self):
        # problem: we need to compare vertices by vertices

        def ngbsOfWrt(u, v):
            ngbs = []
            for e in self.incident_edges(u).values():
                vinside = v in e
                ngbs.append(tuple(sorted(vi for vi in e if vinside or (not vinside and vi != u))))
            return tuple(sorted(ngbs))

        for nds in self.iter_twin_neighbours():
            twins = {}
            reprs = {}
            for u in nds:
                for v in nds:
                    if u >= v:
                        continue
                    elif u in reprs and v in reprs and reprs[u] == reprs[v]:
                        continue
                    elif ngbsOfWrt(u, v) == ngbsOfWrt(v, u):
                        # new representative u for both nodes
                        if v in reprs:
                            reprs[u] = reprs[v]
                            twins[reprs[v]].append(u)
                        elif u in reprs:
                            reprs[v] = reprs[u]
                            twins[reprs[u]].append(v)
                        else:
                            reprs[v] = u
                            reprs[u] = u
                            twins[u] = [u, v]
            for v in twins.values():
                yield v

    #    def maximize_fhec(self, timeout=10):
    #        if z3 is None:
    #            raise ImportError()
    #        solver = z3.Optimize()
    #        solver.set("timeout", timeout)
    #        vars = {}
    #        edges = {}
    #        #rev = {}
    #        start = time.clock()
    #        m = z3.Int(name="cliquesize")
    #
    #        for (k, e) in self.__edges.iteritems():
    #            edges[k] = z3.Real(name="edge{0}".format(k))
    #            solver.add(edges[k] <= 1)
    #            solver.add(edges[k] >= 0)
    #
    #        for v in self.nodes_iter():
    #            vars[v] = z3.Int(name="node{0}".format(v))
    #            #rev[vars[v]] = v
    #            solver.add(vars[v] <= 1)
    #            solver.add(vars[v] >= 0)
    #            solver.add(z3.Or(vars[v] == 0, z3.Sum([edges[k] for k in self.incident_edges(v)]) >= 1))
    #
    #        solver.add(z3.Sum([edges[k] for k in self.__edges]) <= n)
    #        solver.add(z3.Sum([vars[v] for v in self.nodes_iter()]) >= m)
    #        #solver.add(z3.Or([vars[v] == 1 for v in self.nodes_iter()]))
    #        adj = self.adj
    #        for u in self.nodes_iter():
    #            for v in self.nodes_iter():
    #                if u < v and u not in adj[v]:
    #                    solver.add(z3.Or(vars[u] == 0, vars[v] == 0))
    #            if timeout != 0 and time.clock() - start >= timeout:
    #                return None
    #        r = None
    #        try:
    #            #print "solving"
    #            r = solver.maximize(m)
    #            solver.check()
    #        except z3.Z3Exception, e:
    #            logging.error(e.message)
    #        if r is None:
    #            return None
    #
    #        res = solver.lower(r)
    #        #assert(str(res) != 'epsilon' and str(res) != 'unsat' and isinstance(res, z3.IntNumRef) and res.as_long() >= 1)
    #        if str(res) == 'epsilon' or str(res) == 'unsat':
    #            logging.error(res)
    #        elif not isinstance(res, z3.IntNumRef):
    #            logging.error("not an int")
    #        elif res.as_long() < 1:
    #            logging.error("clique result < 1")
    #        else:
    #            cl = [k for (k, v) in vars.iteritems() if solver.model()[v].as_long() == 1]
    #            if len(cl) != res.as_long():
    #                logging.error("{0} vs. {1}".format(len(cl), res.as_long()))
    #                #assert(len(cl) == res.as_long())
    #                return None
    #            return cl
    #        return None
    #

    def largest_hyperedge(self):
        maxe = None
        maxc = 0
        for e in self.__edges.values():
            if len(e) > maxc:
                maxc = len(e)
                maxe = e
        return maxe

    def largest_idx(self):
        maxc = 0
        for e in self.__edges.values():
            if max(e) > maxc:
                maxc = max(e)
        return maxc

    def largest_clique(self, timeout=120):
        if z3 is None:
            raise ImportError()
        solver = z3.Optimize()
        solver.set("timeout", timeout)
        vars = {}
        # rev = {}
        start = time.clock()
        m = z3.Int(name="cliquesize")
        for v in self.nodes_iter():
            vars[v] = z3.Int(name="node{0}".format(v))
            # rev[vars[v]] = v
            solver.add(vars[v] <= 1)
            solver.add(vars[v] >= 0)

        solver.add(z3.Sum([vars[v] for v in self.nodes_iter()]) >= m)
        # solver.add(z3.Or([vars[v] == 1 for v in self.nodes_iter()]))
        adj = self.adj
        for u in self.nodes_iter():
            for v in self.nodes_iter():
                if u < v and u not in adj[v]:
                    solver.add(z3.Or(vars[u] == 0, vars[v] == 0))
            if timeout != 0 and time.clock() - start >= timeout:
                return None
        r = None
        try:
            r = solver.maximize(m)
            solver.check()
        except z3.Z3Exception as e:
            logging.error(e.message)
        if r is None:
            return None

        res = solver.lower(r)
        # assert(str(res) != 'epsilon' and str(res) != 'unsat' and isinstance(res, z3.IntNumRef) and res.as_long() >= 1)
        if str(res) == 'epsilon' or str(res) == 'unsat':
            logging.error(res)
        elif not isinstance(res, z3.IntNumRef):
            logging.error("not an int")
        elif res.as_long() < 1:
            logging.error("clique result < 1")
        else:
            cl = [k for (k, v) in vars.items() if solver.model()[v].as_long() == 1]
            if len(cl) != res.as_long():
                logging.error("{0} vs. {1}".format(len(cl), res.as_long()))
                # assert(len(cl) == res.as_long())
                return None
            # print cl
            return cl
        return None

    # TODO: fixme
    # --solve-limit=<n>[,<m>] : Stop search after <n> conflicts or <m> restarts
    def largest_clique_asp(self, clingoctl=None, timeout=10, enum=True, usc=True, ground=False, prevent_k_hyperedge=3,
                           solve_limit="umax,umax"):
        if clingo is None:
            raise ImportError()

        # TODO:
        # replace with
        # with prg.solve_iter() as it:
        #     for m in it: print
        #     m
        def __on_model(model):
            if len(model.cost) == 0:
                return
            # print model, model.cost, model.optimality_proven
            aset[1] |= model.optimality_proven
            opt = abs(model.cost[0])
            if opt >= aset[0]:
                if opt > aset[0]:
                    aset[2] = []
                aset[0] = opt
                answer_set = [safe_int(x) for x in str(model).translate(str.maketrans('', '', 'u()')).split(" ")]
                # might get "fake" duplicates :(, with different model.optimality_proven
                if answer_set not in aset[2][-1:]:
                    aset[2].append(answer_set)

        prog = StringIO()

        if clingoctl is None:
            c = clingo.Control()

            if usc:
                c.configuration.solver.opt_strategy = "usc,pmres,disjoint,stratify"
                c.configuration.solver.opt_usc_shrink = "min"
            c.configuration.solve.opt_mode = "optN" if enum else "opt"
            c.configuration.solve.models = 0
            c.configuration.solve.solve_limit = solve_limit

            guess = StringIO()
            pos = 0
            sep = lambda ps: " }.\n" if ps == len(self.__vertices) - 1 else ";"
            if len(self.__vertices) > 0:
                guess.write("{")
                prog.write("#maximize {")
                for u in self.__vertices:
                    prog.write(" 1,u({0}):u({1}){2}".format(u, u, sep(pos)))
                    guess.write(" u({0}){1}".format(u, sep(pos)))
                    pos += 1
                prog.write("#show u/1.\n")
                prog.write(guess.getvalue())

            # has to be clique
            if len(self.__edges) > 0:
                if not ground:
                    prog.write(":- u(Y1), u(Y2), not a(Y1, Y2), Y1 < Y2.\n")
                    prog.write("a(Y1, Y2) :- e(X, Y1), e(X, Y2), Y1 < Y2.\n")
                    for k, e in self.__edges.items():
                        for v in e:
                            prog.write("e({0}, {1}).\n".format(k, v))
                else:
                    adj = self.adj
                    for u in self.__vertices:
                        for v in self.__vertices:
                            if u < v and v not in adj[u]:
                                prog.write(":- u({0}), u({1}).\n".format(u, v))
        else:
            c = clingoctl

        aset = [0, False, [], c, []]

        if len(self.__edges) == 0 or len(self.__vertices) == 0:
            return aset

        if not ground and len(self.__edges) > 0:
            prog.write(":- ")
            for i in range(0, prevent_k_hyperedge):
                if i > 0:
                    prog.write(", Y{0} < Y{1}, ".format(i - 1, i))
                prog.write("e(X, Y{0}), u(Y{0})".format(i))
            prog.write(".\n")
            # prog += ":- e(X, Y1), e(X, Y2), e(X, Y3), u(Y1), u(Y2), u(Y3), Y1 < Y2, Y2 < Y3."
        else:
            constr = set()
            for e in self.__edges.values():
                if len(e) <= 2 or len(e) < prevent_k_hyperedge:
                    continue
                # prevent 3 elements from the same edge
                sub = range(0, prevent_k_hyperedge)
                while True:  # sub[0] <= len(e) - prevent_k_hyperedge:
                    rule = []
                    pos = 0
                    # print sub, e
                    for v in sub:
                        rule.append(e[v])
                        pos += 1

                    rule = tuple(sorted(rule))
                    if rule not in constr:
                        constr.add(rule)
                        prog.write(":- " + ", ".join(("u({0})".format(r) for r in rule)) + ".\n")

                    if sub[0] == len(e) - prevent_k_hyperedge:
                        break

                    # next position
                    for i in range(prevent_k_hyperedge - 1, -1, -1):
                        if sub[i] < len(e) + (i - prevent_k_hyperedge):
                            sub[i] += 1
                            for j in range(i + 1, prevent_k_hyperedge):
                                sub[j] = sub[i] + (j - i)
                            break

        # print "XX, ", self.__edges, self.__vertices
        # print(prog.getvalue())

        c.add("prog{0}".format(prevent_k_hyperedge), [], prog.getvalue())

        def solver(c, om):
            c.ground([("prog{0}".format(prevent_k_hyperedge), [])])
            # print "grounded"
            c.solve(on_model=om)

        t = threading.Thread(target=solver, args=(c, __on_model))
        t.start()
        t.join(timeout)
        c.interrupt()
        t.join()

        aset[1] |= c.statistics["summary"]["models"]["optimal"] > 0
        aset[4] = c.statistics
        # print c.statistics
        return aset

    def encoding_clique_guess(self):
        guess = StringIO()
        pos = 0
        sep = lambda ps: " }.\n" if ps == len(self.__vertices) - 1 else ";"

        if len(self.__vertices) > 0:
            guess.write("{ ")
            for u in self.__vertices:
                guess.write(" u({0}){1}".format(u, sep(pos)))
                pos += 1
            guess.write("#show u/1.\n")
        return guess.getvalue()

    # weak constraints: :~ atom, [cost@level,expression]
    # note that higher levels are optimized first
    # we use negative costs to maximize
    def encoding_maximize(self):
        prog = StringIO()
        # sep = lambda pos: " }.\n" if pos == len(self.__vertices) - 1 else ";"

        # pos = 0
        # if len(self.__vertices) > 0:
        #    prog.write("#maximize { ")
        #    for u in self.__vertices:
        #        pos += 1

        prog.write("#maximize { 1,X:u(X) }.")
        # prog.write(":~ u(X). [-1@1,X]")
        return prog.getvalue()

    def encoding_maximize_neighborhood(self):
        prog = StringIO()
        prog.write("#maximize { 1,Y:e(A,Y),e(A,X),u(X) }.\n")
        return prog.getvalue()

    def encoding_maximize_used_hyperedges(self, minimize=False):
        prog = StringIO()

        if len(self.__edges) > 0:
            prog.write("#maximize {{ {0},A:e(A,X),u(X) }}.\n".format(-1 if minimize else 1))
        return prog.getvalue()

    def encoding_maximize_completely_used_hyperedges(self, minimize=False):
        prog = StringIO()

        if len(self.__edges) > 0:
            prog.write("missing(A) :- e(A,U), not u(U).\n")
            prog.write("#maximize { 1,A:missing(A) }.\n" if minimize else "#maximize { 1,A:e(A,_),not missing(A) }.\n")
            # prog.write(":~ missing(A). [-1@1,A]\n" if minimize else ":~ e(A,_), not missing(A). [-1@1,A]\n")
        return prog.getvalue()

    # def encoding_maximize_incompletely_used_hyperedges(self, minimize=False):
    #    prog = StringIO()
    #
    #    if len(self.__edges) > 0:
    #        prog.write("missing(A) :- e(A,U), not u(U).\n")
    #        prog.write("#maximize { 1,A:e(A,X),u(X),missing(A) }.\n" if minimize else "#maximize { 1,A:e(A,X),u(X),not missing(A) }.\n")
    #        #prog.write(":~ missing(A). [-1@1,A]\n" if minimize else ":~ e(A,_), not missing(A). [-1@1,A]\n")
    #    return prog.getvalue()

    def encoding_maximize_exclude_twins(self, twins):
        prog = StringIO()
        sep = lambda ps, l, twin: " }}. [X-1,{0}]\n".format(twin) if ps == l - 1 else ";"

        # prog.write("#maximize { 1-X,Y:tw(Y,X),X>1 }.\n")
        # prog.write(":~ tw(Y,X). [X-1@1,Y]\n")
        pos = 0
        for ts in twins:
            # print(ts)
            prog.write(":~ X>1,X=#count {{ ".format(pos + 1))
            posi = 0
            for t in ts:
                prog.write("1,{0}:u({0}){1}".format(t, sep(posi, len(ts), pos + 1)))
                posi += 1
            pos += 1
        # print(prog.getvalue())
        return prog.getvalue()

    def encoding_largest_clique(self, maximize=True):
        prog = StringIO()

        prog.write(self.encoding_clique_guess())
        if maximize:
            prog.write(self.encoding_maximize())

        # has to be clique
        if len(self.__edges) > 0:
            prog.write(":- u(Y1), u(Y2), not a(Y1, Y2), Y1 < Y2.\n")
            prog.write("a(Y1, Y2) :- e(X, Y1), e(X, Y2), Y1 < Y2.\n")
            for k, e in self.__edges.items():
                for v in e:
                    prog.write("e({0}, {1}).\n".format(k, v))
        return prog.getvalue()

    def encoding_largest_k_hyperclique(self, prevent_k_hyperedge=3, incrementalShot=False):
        prog = StringIO()

        if not incrementalShot:
            prog.write(self.encoding_clique_guess())
            prog.write(self.encoding_maximize())

            # has to be clique
            if len(self.__edges) > 0:
                prog.write(":- u(Y1), u(Y2), not a(Y1, Y2), Y1 < Y2.\n")
                prog.write("a(Y1, Y2) :- e(X, Y1), e(X, Y2), Y1 < Y2.\n")
                for k, e in self.__edges.items():
                    for v in e:
                        prog.write("e({0}, {1}).\n".format(k, v))

        # prog.write(":- e(A,_), #count {{ 1,Y : e(A,Y), u(Y) }} >= {0}.\n".format(prevent_k_hyperedge))
        prog.write(self.encoding_prevent_k_hyperclique(prevent_k_hyperedge))
        return prog.getvalue()

    def encoding_prevent_k_hyperclique(self, prevent_k_hyperedge=3):
        prog = StringIO()

        prog.write(":- ")
        for i in range(0, prevent_k_hyperedge):
            if i > 0:
                prog.write(", Y{0} < Y{1}, ".format(i - 1, i))
            prog.write("e(X, Y{0}), u(Y{0})".format(i))
        prog.write(".\n")
        return prog.getvalue()

    encoder_k_hyperclique = lambda x, k: x.encoding_largest_k_hyperclique(prevent_k_hyperedge=k)
    encoder_largest_clique = lambda x: x.encoding_largest_clique()
    encoder_largest_clique_neighborhood = lambda x: x.encoding_largest_clique() + x.encoding_maximize_neighborhood()
    encoder_largest_clique_wo_twins = lambda x: x.encoding_largest_clique() + x.encoding_maximize_exclude_twins(x.iter_twin_vertices())
    encoder_clique_maximize_used_hyperedges = lambda x: x.encoding_largest_clique(maximize=False) + x.encoding_maximize_used_hyperedges()
    encoder_clique_maximize_completely_used_hyperedges = lambda x: x.encoding_largest_clique(maximize=False) + x.encoding_maximize_completely_used_hyperedges()

    # --solve-limit=<n>[,<m>] : Stop search after <n> conflicts or <m> restarts
    # @deprecated
    def solve_asp(self, encoding, clingoctl=None, timeout=10, enum=False, usc=True, solve_limit="umax,umax"):
        if clingo is None:
            raise ImportError()

        c = clingoctl
        if clingoctl is None:
            c = clingo.Control()
            if usc:
                c.configuration.solver.opt_strategy = "usc,pmres,disjoint,stratify"
                c.configuration.solver.opt_usc_shrink = "min"
            c.configuration.solve.opt_mode = "optN" if enum else "opt"
            c.configuration.solve.models = 0
            c.configuration.solve.solve_limit = solve_limit

        aset = [-sys.maxsize, False, [], c, []]

        # TODO:
        # replace with
        # with prg.solve_iter() as it:
        #     for m in it: print
        #     m
        def __on_model(model):
            if len(model.cost) == 0:
                return
            # print model, model.cost, model.optimality_proven
            aset[1] |= model.optimality_proven
            # invert costs
            opt = -(model.cost[0])
            if opt >= aset[0]:
                if opt > aset[0]:
                    aset[2] = []
                aset[0] = opt
                answer_set = [safe_int(x) for x in str(model).translate(str.maketrans('', '', 'u()')).split(" ")]
                # might get "fake" duplicates :(, with different model.optimality_proven
                if answer_set not in aset[2][-1:]:
                    aset[2].append(answer_set)

        if len(self.__edges) == 0 or len(self.__vertices) == 0:
            return aset

        # print "XX, ", self.__edges, self.__vertices
        # print(encoding)

        c.add("prog", [], encoding)

        def solver(c, om):
            c.ground([("prog", [])])
            # print "grounded"
            c.solve(on_model=om)

        t = threading.Thread(target=solver, args=(c, __on_model))
        t.start()
        t.join(timeout)
        c.interrupt()
        t.join()

        aset[1] |= c.statistics["summary"]["models"]["optimal"] > 0
        aset[4] = c.statistics
        # print c.statistics
        return aset

    def relabel_consecutively(self, revert=True):
        return self.relabel(relab.consecutive_substitution(self.__vertices),
                            relab.consecutive_substitution(self.__edges),
                            revert=revert)

    def relabel(self, substitution, substitution_keys, revert=True):
        self.__vertices = relab.relabel_sequence(self.__vertices, substitution)
        self.__edges = relab.relabel_dict(self.__edges, substitution, substitution_keys)
        if not revert:
            return None, None
        return relab.revert_substitution(substitution), relab.revert_substitution(substitution_keys)

    def fractional_cover(self, verts, solution=None, opt=-1, accuracy=ACCURACY):
        if cx is None:
            raise ImportError()

        if solution is None and len(verts) <= 1:
            return 1.0

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
                                       rhs=[1] * len(constraints))  # ,
        # names=["c{0}".format(x) for x in names])
        if opt >= 0:
            problem.linear_constraints.add(lin_expr=[[names, [1] * len(names)]],
                                           senses=["E"], rhs=[opt])

        problem.set_results_stream(None)
        problem.set_error_stream(None)
        problem.set_warning_stream(None)
        problem.set_log_stream(None)
        problem.solve()
        assert (problem.solution.get_status() == 1)

        if solution is not None:
            pos = 0
            for v in problem.solution.get_values():
                if v >= accuracy:
                    solution[int(names[pos][1:])] = v + accuracy
                pos += 1

        return problem.solution.get_objective_value()
        # print problem.solution.get_values()

    # @staticmethod
    # def project_edge(e, p):
    #    return [x for x in e if x not in p]

    def induce_edges(self, es):
        for k, e in es.items():
            self.add_hyperedge([x for x in e if x in self.__vertices], edge_id=k)

    # can also contract edge parts >= 2, e[0] is the part of the edge that is kept
    def contract_edge(self, e, erepr):
        assert (len(e) >= 2)
        assert (erepr in e)
        dl = -1
        excl = None
        for (k, v) in self.__edges.items():
            contr = [x for x in v if x not in e]
            if len(contr) == 0:  # and contr[0] == e[0]:
                dl = k
            elif (len(contr) + 1 < len(v)) or (len(contr) + 1 == len(v) and erepr not in v):
                excl = erepr
                contr.append(erepr)
                if self.isSubsumed(set(contr), modulo=k):
                    dl = k
                else:
                    self.__edges[k] = Hypergraph.__edge_type(contr)
            elif erepr in v:
                excl = erepr
        if dl >= 0:
            del self.__edges[dl]
        self.__vertices.difference_update(e)
        if excl is not None:
            self.__vertices.update((excl,))

    def incident_edges(self, v):
        edges = {}
        for (e, ge) in self.__edges.items():
            if v in ge:
                edges[e] = ge
        return edges

    def edge_rank(self, n):
        # print self.incident_edges(n).values()
        return list(map(lambda x: (x, len(x)), self.incident_edges(n).values()))

    # @staticmethod
    # def project_edge(e, p):
    #    return [x for x in e if x not in p]

    # def inc(self,v):
    #    nbh = dict()
    #    for e in self.__edges.values():
    #        if v in e:
    #            nbh[e] = Hypergraph.__d
    #    return nbh

    def adjByNode(self, v, strict=True):
        nbh = dict()
        for e in self.__edges.values():
            if v in e:
                for ex in e:
                    if not strict or ex != v:
                        nbh[ex] = Hypergraph.__d
        return nbh

    @property
    def adj(self):
        nbhs = dict()
        for k in self.__vertices:
            nbhs[k] = self.adjByNode(k)
        return nbhs

    def __delitem__(self, v):
        # please do not make me copy everything :(
        # assert(Hypergraph.__edge_type == type(list))
        self.__vertices.remove(v)
        # del self.__vertices[v]
        dl = []
        for k, e in self.__edges.items():
            if v in self.__edges[k]:
                # thank you, tuple!
                # del self.__edges[k][v]
                e = set(e)
                e.remove(v)
                self.__edges[k] = Hypergraph.__edge_type(e)
                # print self.__edges[k]
                dl.append((k, e))
        for k, e in dl:
            if len(e) <= 1 or self.isSubsumed(e, modulo=k):
                del self.__edges[k]

    def number_of_edges(self):
        return len(self.__edges)

    def size_largest_hyperedge(self):
        ret = 0
        for i in self.__edges:
            ret = max(ret, len(self.__edges[i]))
        return ret

    def number_of_nodes(self):
        return len(self.__vertices)

    def edges_iter(self):
        return iter(self.__edges.values())

    # bool operator so to say
    def __nonzero__(self):
        return True
        # return len(self.__edges) > 0

    def __copy__(self):
        hg = Hypergraph(non_numerical=self.__non_numerical, vertices=self.__vertices)
        hg.__edges = self.__edges
        if self.__non_numerical:
            hg.__nsymtab = self.__nsymtab
            hg.__elabel = self.__elabel

    def __deepcopy__(self, memodict=None):
        # assert(False)
        if memodict is None:
            memodict = {}
        hg = Hypergraph(non_numerical=self.__non_numerical, vertices=copy.deepcopy(self.__vertices, memodict))
        hg.__edges = copy.deepcopy(self.__edges, memodict)
        if self.__non_numerical:
            # do not deep copy this stuff, not needed for now
            hg.__nsymtab = self.__nsymtab
            hg.__elabel = self.__elabel
        return hg

    def copy(self):
        return copy.deepcopy(self)

    # TODO: copy?
    # @property
    def nodes(self):
        return self.__vertices

    # TODO: copy?
    # @property
    def edges(self):
        # return {}
        # raise RuntimeError
        # print(dir(self.__edges))
        # exit(1)
        return self.__edges
        # return copy.deepcopy(self.__edges)

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
                is_dimacs = line[1] == 'edge' or "htd" in line[1]
            elif line[0] != 'c':
                if is_dimacs:
                    HG.add_hyperedge(list(map(int, line[1:])))
                else:
                    HG.add_hyperedge(list(map(int, line)))

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
            # replace whitespaces
            line = line.replace(' ', '')

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

    @classmethod
    def fromstream_fischlformat_re(clazz, stream):
        HG = clazz(non_numerical=True)
        istream = ''.join(stream.readlines()).replace('\n', ' ')
        for line in re.findall(r'(\w+\s*\((\s*\w+\s*,\s*)*\w+\s*\)\s*)', istream):
            line = line[0]
            edge_name = None
            edge_vertices = []
            # replace whitespaces
            line = line.replace(' ', '')

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
    def from_file(clazz, filename, strict=False, fischl_format=False):
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
        try:
            mtype = mimetypes.guess_type(filename)[1]
            if mtype is None:
                stream = open(filename, 'r')
            elif mtype == 'bzip2':
                stream = BZ2File(filename, 'r')
            elif mtype == 'gz':
                stream = gzip.open(filename, 'r')
            # TODO(jf): migration
            elif mtype == 'xz':
                stream = lzma.open(filename, 'r')
            else:
                raise IOError('Unknown input type "%s" for file "%s"' % (mtype, filename))
            if fischl_format:
                hypergraph_old = Hypergraph.fromstream_fischlformat(stream)
                stream.seek(0)
                hypergraph = Hypergraph.fromstream_fischlformat_re(stream)
                if hypergraph_old.number_of_nodes() != hypergraph.number_of_nodes() and \
                        hypergraph_old.number_of_edges() != hypergraph.number_of_edges():
                    logging.error(
                        f"Hypergraph mismatch between old and new reader (#nodes/#hedges). "
                        f"Old:{hypergraph_old.number_of_nodes()}/{hypergraph_old.number_of_edges()} "
                        f"New:{hypergraph.number_of_nodes()}/{hypergraph.number_of_edges()}")
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

    def add_hyperedge(self, X, name=None, edge_id=None, checkSubsumes = True):
        if len(X) <= 1:
            return
        if self.__non_numerical:
            X = list(map(self.__nsymtab.get, X))
        if edge_id is None:
            edge_id = len(self.__edges) + 1

        if self.__non_numerical and name is not None:
            self.__elabel[edge_id] = name

        # remove/avoid already subsets of edges
        if not checkSubsumes or not self.isSubsumed(set(X), checkSubsumes=True):
            self.__edges[edge_id] = Hypergraph.__edge_type(X)
            self.__vertices.update(list(X))
        # else:
        #    print("subsumed: ", X)
        return X

    def isSubsumed(self, sx, checkSubsumes=False, modulo=-1):
        for k, e in self.__edges.items():
            if k == modulo:
                continue
            elif sx.issubset(e):
                return True
            elif checkSubsumes and sx.issuperset(e):  # reset the edge
                # print sx, e
                # self.__edges[k][:] = sx
                self.__edges[k] = Hypergraph.__edge_type(sx)
                self.__vertices.update(sx)
                return True
        return False

    def edge_iter(self):
        return iter(self.__edges.keys())

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

    def write_graph(self, stream, dimacs=False, non_dimacs='htw', print_id=False):
        """
        :param stream: stream where to output the hypergraph
        :type stream: cString
        :param dimacs: write dimacs header (or gr header)
        :type dimacs: bool
        :rtype Graph, dict
        :return: written hypergraph, remapping of vertices from old hypergraph
        """
        gr_string = 'edge' if dimacs else non_dimacs 
        s = 'p ' if dimacs else ''
        stream.write(('p %s %s %s\n' % (gr_string, self.largest_idx(), self.number_of_edges())).encode())
        s = 'e ' if dimacs else ''
        for e_id, nodes in zip(range(self.number_of_edges()), self.edges_iter()):
            nodes = ' '.join(list(map(str, nodes)))
            if print_id:
                stream.write(('%s%s %s\n' % (s, e_id + 1, nodes)).encode())
            else:
                stream.write(('%s%s\n' % (s, nodes)).encode())
        stream.flush()

    def __str__(self):
        string = StringIO()
        self.write_gr(string)
        return string.getvalue()

    def __repr__(self):
        return self.__str__()
