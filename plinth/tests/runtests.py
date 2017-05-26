#!/usr/bin/python3
#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Module for Django pre-test configuration and setup.
"""

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def run_tests(pattern=None, return_to_caller=False):
    """Set up the Django test environment and run the specified tests."""
    os.environ['DJANGO_SETTINGS_MODULE'] = \
        'plinth.tests.data.django_test_settings'
    django.setup()
    test_runner_cls = get_runner(settings)
    test_runner = test_runner_cls()

    if pattern is None:
        pattern_list = [
            'plinth/tests',
            'plinth/modules',
        ]
    else:
        pattern_list = [pattern]

    failures = test_runner.run_tests(pattern_list)
    if failures > 0 or not return_to_caller:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_tests()
