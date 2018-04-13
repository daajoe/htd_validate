#!/usr/bin/env false
from __future__ import absolute_import
import htd_validate

import logging
import htd_validate_tests.tests.utils.validateGraph_testcase as vtd
import os
import htd_validate.utils.hypergraph

class TestHypergraph(vtd.ValidateGraphTestCase):
    _gr_classname = htd_validate.Hypergraph.__name__
    _type = "Hypergraph"

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def tearDown(self):
        pass

    def testTwins(self):
        hg = self.loadFile(self.filePath("testHG/") + "C13_7.edge")
        print list(hg.iter_twin_vertices())
        assert False

    def testAdj(self):
        hg = self.loadFile(self.filePath("testHG/") + "C13_7.edge")
        self.assertIsNotNone(hg)
        self.assertEqual([1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], sorted(hg.adj[2].keys()))
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], sorted(hg.adj[13].keys()))

    def testDel(self):
        hg = self.loadFile(self.filePath("testHG/") + "C13_7.edge")
        del hg[13]
        self.assertEqual([1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], sorted(hg.adj[2].keys()))
        self.assertEqual([1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], sorted(hg.adj[2].keys()))

    def testFractionalCover(self):
        sol = {}
        hg = self.loadFile(self.filePath("testHG/") + "C13_7.edge")
        self.assertEqual(1.0, hg.fractional_cover([2, 13], solution=sol))

        logging.debug(sol)
        self.assertEqual(1, len(sol))

        hg = self.loadFile(self.filePath("testHG/") + "C3.edge")
        sol = {}
        self.assertEqual(1.5, hg.fractional_cover([1, 2, 3], solution=sol))
        logging.debug(sol)
        self.assertEqual(3, len(sol))
        sol = {}
        self.assertEqual(1.0, hg.fractional_cover([1, 2], solution=sol))
        logging.debug(sol)
        self.assertEqual(1, len(sol))

        hg = self.loadFile(self.filePath("testHG/") + "C4.edge")
        sol = {}
        self.assertEqual(2.0, hg.fractional_cover([1, 2, 3, 4], solution=sol))
        logging.debug(sol)
        self.assertEqual(2, len(sol))

    def maxCliqueFromFile(self, maxC, fil, fischl_format=False, ground=False):
        hg = self.loadFile(fil, fischl_format=fischl_format)
        self.assertIsNotNone(hg)
        #if len(hg.nodes()) >= 400:
        #    return
        #print hg.edges()

        aset = hg.largest_clique_asp(timeout=2, enum=True, ground=ground)
        maxC[0] = max(maxC[0], aset[0])
        if aset[1] == False:
            maxC[1] += 1

        print maxC[0], len(aset[2]), aset
        #print maxC

    def testLargestClique(self):
        mx = [0, 0]
        self.maxCliqueFromFile(mx, self.filePath("testHG/") + "Nonogram-001-table.xml.hg",
                                    fischl_format=True, ground=False)
        self.maxCliqueFromFile(mx, self.filePath("testHG/") + "C13_7.edge")

        doRealLifeTests = False
        if doRealLifeTests:
            #path, dirs, files
            for path, dirs, _ in os.walk(self.filePath("../../../../../../hypergraphs/hyperbench/")):
                #print dirs
                for d in dirs:
                    for _, _, files in os.walk(os.path.join(path, d)):
                        for f in files:
                            print d + "/" + f
                            self.maxCliqueFromFile(mx, self.filePath("../../../../../../hypergraphs/hyperbench/" + d + "/") + f,
                                                    fischl_format=True, ground=False)
        print mx
