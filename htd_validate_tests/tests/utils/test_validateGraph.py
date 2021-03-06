#!/usr/bin/env false
from __future__ import absolute_import
import htd_validate

import htd_validate_tests.tests.utils.validateGraph_testcase as vtd
from htd_validate.decompositions import Decomposition


class TestValidateTD(vtd.ValidateGraphTestCase):
    _gr_classname = htd_validate.Graph.__name__

    def test_valid(self):
        # Inputs that have a valid decomposition
        self.validateFolder("valid", True)

    def test_invalid_spec(self):
        # Inputs that have an invalid
        self.validateFolder("invalid_spec", assertion=3, strict=False)

    def test_invalid_spec_strict(self):
        # Inputs that have an invalid
        self.validateFolder("invalid_spec_strict", assertion=3, strict=True)
