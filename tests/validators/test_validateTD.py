#!/usr/bin/env false

import validateTD_testcase as vtd


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
