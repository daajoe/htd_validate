#!/usr/bin/env false
from htd_validate.decompositions import HypertreeDecomposition
from htd_validate.validators.validator import Validator

class HypertreeDecompositionValidator(Validator):
    _baseclass = HypertreeDecomposition
