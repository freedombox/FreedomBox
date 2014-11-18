#!/usr/bin/python3
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

"""Support for integration of code test coverage analysis with setuptools.

Derived from 'Adding Test Code Coverage Analysis to a Python Project’s Setup Command'
<http://jeetworks.org/adding-test-code-coverage-analysis-to-a-python-projects-setup-command/>
"""

import coverage
import glob
import setuptools
import shutil
import time
import unittest

from plinth import tests


# project directories with testable source code
SOURCE_DIRS = ['plinth'] + glob.glob('plinth/modules/*')

# files to exclude from coverage analysis and reporting
FILES_TO_OMIT = ['plinth/tests/*.py']

# location of coverage HTML report files
COVERAGE_REPORT_DIR = 'plinth/tests/coverage/report'


class TestCoverageCommand(setuptools.Command):
    """
    Subclass of setuptools Command to perform code test coverage analysis.
    """

    description = "Run test coverage analysis"
    user_options = [
        ('test-module=', 't', "Explicitly specify a single module to test")
    ]

    def initialize_options(self):
        """
        Initialize options to default values.
        """
        self.test_module = None

    def finalize_options(self):
        pass

    def run(self):
        """
        Main command implementation.
        """

        # erase any existing HTML report files
        try:
            shutil.rmtree(COVERAGE_REPORT_DIR, True)
        except:
            pass

        # initialize a test suite for one or all modules
        if self.test_module is None:
            test_suite = tests.TEST_SUITE
        else:
            test = unittest.defaultTestLoader.loadTestsFromNames([self.test_module])
            test_suite = unittest.TestSuite(test)

        # run the coverage analysis
        runner = unittest.TextTestRunner()
        cov = coverage.coverage(auto_data=True, branch=True, source=SOURCE_DIRS,
                                omit=FILES_TO_OMIT)
        cov.erase()     # erase existing coverage data file
        cov.start()
        runner.run(test_suite)
        cov.stop()

        # generate an HTML report
        html_report_title = ("FreedomBox:Plinth -- Test Coverage as of " +
                             time.strftime("%x %X %Z"))
        cov.html_report(directory=COVERAGE_REPORT_DIR, omit=FILES_TO_OMIT,
                        title=html_report_title)
