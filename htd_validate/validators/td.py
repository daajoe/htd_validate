#!/usr/bin/env false

from validator import Validator
import htd_validate as dv

class TreeDecompositionValidator(Validator):
    def __init__(self):
        super(TreeDecompositionValidator, self).__init__()

    def decomposition_type(self):
        return dv.decompositions.TreeDecomposition.__name__

    def graph_type(self):
        return dv.decompositions.TreeDecomposition.graph_type()