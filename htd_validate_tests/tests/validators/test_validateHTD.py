#!/usr/bin/env false
from __future__ import absolute_import
import htd_validate_tests.tests.validators.test_validateTD as vtd

import htd_validate.utils as grap
import htd_validate.decompositions as dec

class TestValidateHTD(vtd.TestValidateTD):
    _td = "htd"
    #TODO: uniform hgr format
    _gr = "edge"
    _td_classname = dec.HypertreeDecomposition.__name__
    _gr_classname = grap.Hypergraph.__name__
