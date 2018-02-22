#!/usr/bin/env false

import test_validateTD as vtd

import htd_validate.utils as grap
import htd_validate.decompositions as dec

class TestValidateHTD(vtd.TestValidateTD):
    _td = "htd"
    #TODO: uniform hgr format
    _gr = "edge"
    _td_classname = dec.HypertreeDecomposition.__name__
    _gr_classname = grap.Hypergraph.__name__
