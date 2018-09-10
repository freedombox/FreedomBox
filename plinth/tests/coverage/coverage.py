#!/usr/bin/python3
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-
#
# This file is part of FreedomBox.
#
# Derived from code sample at:
# http://jeetworks.org/adding-test-code-coverage-analysis-to-a-python-projects-setup-command/
#
# Copyright 2009 Jeet Sukumaran and Mark T. Holder.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Support for integration of code test coverage analysis with setuptools.
"""

import glob
import setuptools
import shutil
import time


# Project directories with testable source code
SOURCE_DIRS = ['plinth'] + glob.glob('plinth/modules/*')

# Files to exclude from coverage analysis and reporting
FILES_TO_OMIT = [
    'plinth/tests/*.py',
    'plinth/modules/*/tests/*.py'
]

# Location of coverage HTML report files
COVERAGE_REPORT_DIR = 'plinth/tests/coverage/report'


class CoverageCommand(setuptools.Command):
    """
    Subclass of setuptools Command to perform code test coverage analysis.
    """

    description = 'Run test coverage analysis'
    user_options = [
        ('test-module=', 't', 'Explicitly specify a single module to test')
    ]

    def initialize_options(self):
        """Initialize options to default values."""
        self.test_module = None

    def finalize_options(self):
        pass

    def run(self):
        """Main command implementation."""
        import coverage

        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(
                self.distribution.install_requires)

        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(
                self.distribution.tests_require)

        # Erase any existing HTML report files
        try:
            shutil.rmtree(COVERAGE_REPORT_DIR, True)
        except Exception:
            pass

        # Run the coverage analysis
        cov = coverage.coverage(auto_data=True, config_file=True,
                                source=SOURCE_DIRS, omit=FILES_TO_OMIT)
        cov.erase()     # Erase existing coverage data file
        cov.start()
        # Invoke the Django test setup and test runner logic
        from plinth.tests.runtests import run_tests
        run_tests(pattern=self.test_module, return_to_caller=True)
        cov.stop()

        # Generate an HTML report
        html_report_title = 'FreedomBox -- Test Coverage as of ' + \
                            time.strftime('%x %X %Z')
        cov.html_report(directory=COVERAGE_REPORT_DIR, omit=FILES_TO_OMIT,
                        title=html_report_title)

        # Print a detailed console report with the overall coverage percentage
        print()
        cov.report(omit=FILES_TO_OMIT)

        # Print the location of the HTML report
        print('\nThe HTML coverage report is located at {}.'.format(
            COVERAGE_REPORT_DIR))
