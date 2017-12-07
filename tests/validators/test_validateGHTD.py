#!/usr/bin/env false

import test_validateTD as vtd


class TestValidateGHTD(vtd.TestValidateTD):
    _td = "ghtd"
    _gr = "edge"
    _td_classname = "GeneralizedHypertreeDecomposition"
    _gr_classname = "Hypergraph"
