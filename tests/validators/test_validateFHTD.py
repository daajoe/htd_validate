#!/usr/bin/env false

import test_validateTD as vtd


class TestValidateFHTD(vtd.TestValidateTD):
    _td = "fhtd"
    #TODO: uniform hgr format
    _gr = "edge"
    _td_classname = "FractionalHypertreeDecomposition"
    _gr_classname = "Hypergraph"
