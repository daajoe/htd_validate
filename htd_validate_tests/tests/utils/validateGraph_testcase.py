#!/usr/bin/env false

from __future__ import absolute_import

import os
import unittest

import htd_validate.decompositions
import htd_validate.utils


class ValidateGraphTestCase(unittest.TestCase):
    _gr = "gr"
    _type = "Graph"
    _gr_classname = htd_validate.utils.Graph.__name__  #'missing'

    def loadFile(self, graph_file, strict=False, fischl_format=False):
        return getattr(htd_validate.utils, self._gr_classname).from_file(graph_file, strict=strict, fischl_format=fischl_format)

    def assertFromFiles(self, graph_file, assertion=True, strict=False):
        if assertion not in [True, False]:
            with self.assertRaises(SystemExit):
                self.loadFile(graph_file, strict)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def filePath(self, folder):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), self._type, folder)

    def validateFolder(self, folder, assertion=True, strict=False):
        folder = self.filePath(folder)
        print("checking folder: ", folder)
        for subdir, dirs, files in os.walk(folder):
            for file in sorted(files):
                print("testing: ", file, file)
                self.assertFromFiles(os.path.join(folder, file), assertion, strict)

    def mapBenchmarks(self, rel_path, function, args={}):
        #path, dirs, files
        for path, dirs, _ in os.walk(self.filePath(rel_path)):
            #print dirs
            for d in dirs:
                for _, _, files in os.walk(os.path.join(path, d)):
                    for f in files:
                        print d + "/" + f
                        args["path"] = self.filePath("./hyperbench/" + d + "/") + f
                        function(args)
                        #self.maxCliqueFromFile(mx, self.filePath("../../../../../hypergraphs/hyperbench/" + d + "/") + f,
                        #                        fischl_format=True, ground=False)

