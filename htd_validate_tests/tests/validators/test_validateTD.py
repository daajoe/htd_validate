#!/usr/bin/env false
from __future__ import absolute_import
import htd_validate_tests.tests.validators.validateTD_testcase as vtd
import htd_validate.decompositions.td as td

class TestValidateTD(vtd.ValidateTDTestCase):

    def test_valid(self):
        # Inputs that have a valid decomposition
        self.validateFolder("valid", True)

    def test_solver_bugs(self):
        # Inputs that are invalid and have been seen by solvers
        self.validateFolder("solver-bugs", False)

    def test_should_be_valid(self):
        # Inputs that should be valid
        self.validateFolder("should_be_valid", True)

    def test_invalid(self):
        # Inputs that have an invalid decomposition
        self.validateFolder("invalid", assertion=False, strict=False)

    def test_invalid_spec(self):
        # Inputs that violate the PACE td format spec (some relaxed version)
        self.validateFolder("invalid_spec", assertion=2)

    def test_invalid_spec_strict(self):
        # Inputs that violate the PACE td format spec (strict PACE requirements)
        self.validateFolder("invalid_spec_strict", assertion=2, strict=True)

    def test_invalid_format(self):
        # Inputs that have an invalid input regardless spec details
        self.validateFolder("invalid_format", assertion=2)

    def test_controversial(self):
        # Inputs where format requirements might be seen as controversial
        self.validateFolder("controversial", True or False)

    def tdFromGraph(self, graph_file, maxbag, ord=None):
        g = self.loadFile(self.filePath("testTD/") + graph_file)
        self.assertIsNotNone(g)
        #if ord is None:
        #    ord = range(g.number_of_nodes() + 1)
        tdx = td.TreeDecomposition.from_ordering(g, ord)
        print tdx.chi, tdx.T.edges()
        #tdx.show(2)
        self.assertEqual(maxbag, tdx.max_bag_size())
        self.assertTrue(tdx.validate(g))
        return tdx


    def test_treedecomposition(self):
        if self._td_classname != td.TreeDecomposition.__name__:
            return
        self.tdFromGraph("C3.gr", 3)
        self.tdFromGraph("C4.gr", 4)
        self.tdFromGraph("CPath4.gr", 2)
        self.tdFromGraph("C1_1.gr", 4, [6, 2, 4, 1, 3, 5])
        self.tdFromGraph("C1_1.gr", 4, [6, 5, 4, 3, 2, 1])
