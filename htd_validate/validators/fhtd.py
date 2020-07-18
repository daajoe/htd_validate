#!/usr/bin/env false
from htd_validate.decompositions import FractionalHypertreeDecomposition
from htd_validate.validators.validator import Validator


class FractionalHypertreeDecompositionValidator(Validator):
    _baseclass = FractionalHypertreeDecomposition
