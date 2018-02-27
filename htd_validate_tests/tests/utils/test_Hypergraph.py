#!/usr/bin/env false
from __future__ import absolute_import
import htd_validate

import htd_validate_tests.tests.utils.validateGraph_testcase as vtd
import os
import htd_validate.utils.hypergraph

class TestHypergraph(vtd.ValidateGraphTestCase):
    _gr_classname = htd_validate.Hypergraph.__name__
    _type = "Hypergraph"

    def setUp(self):
        pass

    def tearDown(self):
        pass

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
        hg = self.loadFile(self.filePath("testHG/") + "C13_7.edge")
        self.assertEqual(1.0, hg.fractional_cover([2, 13]))

        hg = self.loadFile(self.filePath("testHG/") + "C3.edge")
        self.assertEqual(1.5, hg.fractional_cover([1, 2, 3]))
        self.assertEqual(1.0, hg.fractional_cover([1, 2]))

        hg = self.loadFile(self.filePath("testHG/") + "C4.edge")
        self.assertEqual(2.0, hg.fractional_cover([1, 2, 3, 4]))

    def testLargestClique(self):
        hg = self.loadFile(self.filePath("testHG/") + "C13_7.edge")
        hg.largest_clique_asp(solve_limit="20,20")
