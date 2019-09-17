#!/usr/bin/env false
from htd_validate.decompositions import TreeDecomposition
from htd_validate.validators.validator import Validator


class TreeDecompositionValidator(Validator):
    _baseclass = TreeDecomposition
