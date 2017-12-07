#!/usr/bin/env false

import validatetd_testcase as vtd


class TestValidateTD(vtd.ValidateTDTestCase):

    def test_valid(self):
        self.validateFolder("valid", True)

    def test_solver_bugs(self):
        self.validateFolder("solver-bugs", False)

    def test_empty(self):
        self.validateFolder("empty", False)

    def test_invalid(self):
        self.validateFolder("invalid", False)
