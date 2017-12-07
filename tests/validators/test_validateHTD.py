#!/usr/bin/env false

import test_validateTD as vtd


class TestValidateHTD(vtd.TestValidateTD):
    _td = "htd"
    #TODO: uniform hgr format
    _gr = "edge"
    _td_classname = "HypertreeDecomposition"
    _gr_classname = "Hypergraph"
