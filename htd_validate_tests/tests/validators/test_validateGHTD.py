#!/usr/bin/env false

import test_validateTD as vtd

import htd_validate.utils as grap
import htd_validate.decompositions as dec


class TestValidateGHTD(vtd.TestValidateTD):
    _td = "ghtd"
    #TODO: uniform hgr format
    _gr = "edge"
    _td_classname = dec.GeneralizedHypertreeDecomposition.__name__
    _gr_classname = grap.Hypergraph.__name__
