#!/usr/bin/env false

from __future__ import absolute_import

import os
import unittest

import htd_validate.decompositions
import htd_validate.utils


class ValidateTDTestCase(unittest.TestCase):
    _td = "td"
    _gr = "gr"
    _td_classname = "TreeDecomposition"
    _gr_classname = "Graph"

    def assertFromFiles(self, graph_file, td_file, assertion=True, strict=False):
        def _assertValidate():
            hg = getattr(htd_validate.utils, self.__class__._gr_classname).from_file(graph_file)
            decomp = getattr(htd_validate.decompositions, self.__class__._td_classname).from_file(filename=td_file,
                                                                                                      strict=strict)
            self.assertEqual(assertion, decomp.validate(hg),
                                 "td validation result wrong, should be: %s in: %s" % (assertion, td_file))

        if assertion not in [True, False]:
            with self.assertRaises(SystemExit):
                _assertValidate()
        else:
            _assertValidate()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def validateFolder(self, folder, assertion=True, strict=False):
        graph = None
        folder = os.path.dirname(os.path.realpath(__file__)) + "/" + self.__class__._td + "/" + folder + "/"
        print("checking folder: ", folder)
        for subdir, dirs, files in os.walk(folder):
            for file in sorted(files):
                if file.endswith(self.__class__._gr):
                    if graph is not None:
                        self.assertEqual(False, True, "td file missing for graph file: " + graph)
                    graph = file
                elif file.endswith(self.__class__._td):
                    if graph is None:
                        self.assertEqual(False, True, "graph file missing for td file: " + file)
                    else:
                        print("testing: ", graph, file)
                        self.assertFromFiles(folder + graph, folder + file, assertion, strict)
                    graph = None
