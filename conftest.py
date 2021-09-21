# SPDX-License-Identifier: AGPL-3.0-or-later
"""
pytest configuration for all tests.
"""

import importlib
import os
import pathlib
import sys
from unittest.mock import patch

import pytest

try:
    importlib.import_module('pytest_bdd')
    _bdd_available = True
except ImportError:
    _bdd_available = False
else:
    from plinth.tests.functional.step_definitions import *


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
        if 'functional' in item.keywords or (item.parent.fspath.basename
                                             and item.parent.fspath.basename
                                             == 'test_functional.py'):
            item.add_marker(skip_functional)


@pytest.fixture(name='load_cfg')
def fixture_load_cfg():
    """Load test configuration."""
    from plinth import cfg

    keys = ('file_root', 'config_dir', 'data_dir', 'custom_static_dir',
            'store_file', 'actions_dir', 'doc_dir', 'server_dir', 'host',
            'port', 'use_x_forwarded_for', 'use_x_forwarded_host',
            'secure_proxy_ssl_header', 'box_name', 'develop')
    saved_state = {}
    for key in keys:
        saved_state[key] = getattr(cfg, key)

    root_dir = pathlib.Path(__file__).resolve().parent
    cfg_file = root_dir / 'plinth' / 'develop.config'
    cfg.read_file(str(cfg_file))
    yield cfg

    for key in keys:
        setattr(cfg, key, saved_state[key])


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


@pytest.fixture(scope='session')
def splinter_selenium_implicit_wait():
    """Disable implicit waiting."""
    return 0


@pytest.fixture(scope='session')
def splinter_wait_time():
    """Disable explicit waiting."""
    return 0.01


@pytest.fixture(scope='session')
def splinter_browser_load_condition():
    """When a page it loaded, wait until <body> is available."""

    def _load_condition(browser):
        if browser.url == 'about:blank':
            return True

        ready_state = browser.execute_script('return document.readyState;')
        return ready_state == 'complete'

    return _load_condition


@pytest.fixture(name='actions_module', scope='module')
def fixture_actions_module(request):
    """Import and return an action module."""
    actions_name = getattr(request.module, 'actions_name')
    actions_file = str(
        pathlib.Path(__file__).parent / 'actions' / actions_name)

    loader = importlib.machinery.SourceFileLoader(actions_name, actions_file)
    spec = importlib.util.spec_from_loader(actions_name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[actions_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name='call_action')
def fixture_call_action(request, capsys, actions_module):
    """Run actions with custom root path."""

    actions_name = getattr(request.module, 'actions_name')

    def _call_action(*args, **_kwargs):
        if isinstance(args[0], list):
            argv = [actions_name] + args[0]  # Command line style usage
        else:
            argv = [args[0]] + args[1]  # superuser_run style usage

        with patch('argparse._sys.argv', argv):
            actions_module.main()
            captured = capsys.readouterr()
            return captured.out

    return _call_action
