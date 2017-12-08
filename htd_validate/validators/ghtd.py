#!/usr/bin/env false

from validator import Validator
import htd_validate as dv

class GeneralizedHypertreeDecompositionValidator(Validator):
    def __init__(self):
        super(GeneralizedHypertreeDecompositionValidator, self).__init__()

    def decomposition_type(self):
        return dv.decompositions.GeneralizedHypertreeDecomposition.__name__

    def graph_type(self):
        return dv.decompositions.GeneralizedHypertreeDecomposition.graph_type()