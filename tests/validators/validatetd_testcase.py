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

    def assertFromFiles(self,graph_file, td_file, assertTrue=True):
        hg = getattr(htd_validate.utils, self.__class__._gr_classname).from_file(graph_file)
        if assertTrue not in [True, False]:
            with self.assertRaises(SystemExit):
                decomp = getattr(htd_validate.decompositions, self.__class__._td_classname).from_file(td_file, True)
                self.assertEqual(assertTrue, decomp.validate(hg),
                                 "td validation result wrong, should be: " + str(assertTrue) + " in: " + td_file)
        else:
            decomp = getattr(htd_validate.decompositions, self.__class__._td_classname).from_file(td_file, True)
            self.assertEqual(assertTrue, decomp.validate(hg), "td validation result wrong, should be: " + str(assertTrue) + " in: " + td_file)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def validateFolder(self, folder, assertTrue=True):
        #print self.__class__.__name__
        graph = None
        #print str(Path.cwd().iterdir())
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
                        #print("testing: ", graph, file)
                        self.assertFromFiles(folder+graph, folder+file, assertTrue)
                    graph = None