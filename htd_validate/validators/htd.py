#!/usr/bin/env false

from validator import Validator
import htd_validate as dv


class HypertreeDecompositionValidator(Validator):
    def __init__(self):
        super(HypertreeDecompositionValidator, self).__init__()

    def decomposition_type(self):
        return dv.decompositions.HypertreeDecomposition.__name__

    def graph_type(self):
        return dv.decompositions.HypertreeDecomposition.graph_type()
