#!/usr/bin/env false

from validator import Validator
import htd_validate as dv


class FractionalHypertreeDecompositionValidator(Validator):
    def __init__(self):
        super(FractionalHypertreeDecompositionValidator, self).__init__()

    def decomposition_type(self):
        return dv.decompositions.FractionalHypertreeDecomposition.__name__

    def graph_type(self):
        return dv.decompositions.FractionalHypertreeDecomposition.graph_type()
