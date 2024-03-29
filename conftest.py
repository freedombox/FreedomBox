# SPDX-License-Identifier: AGPL-3.0-or-later
"""
pytest configuration that needs to be pytest rootdir.
"""


def pytest_addoption(parser):
    """Add a command line option to run functional tests."""
    parser.addoption('--include-functional', action='store_true',
                     default=False, help='Run functional tests also')
