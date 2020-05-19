# SPDX-License-Identifier: AGPL-3.0-or-later
"""
pytest configuration for all tests.
"""

import importlib
import os
import pathlib

import pytest

try:
    importlib.import_module('pytest_bdd')
    _bdd_available = True
except ImportError:
    _bdd_available = False
else:
    from plinth.tests.functional.step_definitions.application import *
    from plinth.tests.functional.step_definitions.interface import *
    from plinth.tests.functional.step_definitions.service import *
    from plinth.tests.functional.step_definitions.site import *
    from plinth.tests.functional.step_definitions.system import *


def pytest_ignore_collect(path, config):
    """Return True to ignore functional tests."""
    if path.basename == 'test_functional.py':
        return not _bdd_available


def pytest_addoption(parser):
    """Add a command line option to run functional tests."""
    parser.addoption('--include-functional', action='store_true',
                     default=False, help='Run functional tests also')


def pytest_collection_modifyitems(config, items):
    """Filter out functional tests unless --include-functional is passed."""
    if config.getoption('--include-functional'):
        # Option provided on command line, no filtering
        return

    skip_functional = pytest.mark.skip(
        reason='--include-functional not provided')
    for item in items:
        if 'functional' in item.keywords or (
                item.parent.fspath.basename
                and item.parent.fspath.basename == 'test_functional.py'):
            item.add_marker(skip_functional)


@pytest.fixture(name='load_cfg')
def fixture_load_cfg():
    """Load test configuration."""
    from plinth import cfg

    root_dir = pathlib.Path(__file__).resolve().parent
    test_data_dir = root_dir / 'plinth' / 'tests' / 'data'
    cfg_file = test_data_dir / 'etc' / 'plinth' / 'plinth.config'
    cfg.read(str(cfg_file), str(root_dir))
    yield cfg
    cfg.read()


@pytest.fixture(name='develop_mode')
def fixture_develop_mode(load_cfg):
    """Turn on development mode for a test."""
    load_cfg.develop = True
    yield
    load_cfg.develop = False


@pytest.fixture(name='needs_root', scope='session')
def fixture_needs_root():
    """Skip test if not running in root mode."""
    if os.geteuid() != 0:
        pytest.skip('Needs to be root')


@pytest.fixture(name='needs_not_root', scope='session')
def fixture_needs_not_root():
    """Skip test if running in root mode."""
    if os.geteuid() == 0:
        pytest.skip('Needs not to be root')


@pytest.fixture(name='needs_sudo')
def fixture_needs_sudo():
    """Skip test if sudo command is not available."""
    if not os.path.isfile('/usr/bin/sudo'):
        pytest.skip('Needs sudo command installed.')
