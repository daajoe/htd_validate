#!/usr/bin/env false
from htd_validate.decompositions import GeneralizedHypertreeDecomposition
from htd_validate.validators.validator import Validator


class GeneralizedHypertreeDecompositionValidator(Validator):
    _baseclass = GeneralizedHypertreeDecomposition
