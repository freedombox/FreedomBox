#
# This file is part of FreedomBox.
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
pytest configuration for all tests.
"""

import os
import pathlib

import pytest


def pytest_addoption(parser):
    """Add a command line option to run functional tests."""
    parser.addoption('--include-functional', action='store_true',
                     default=False, help='Run functional tests also')


def pytest_collection_modifyitems(config, items):
    """Filter out functional tests unless --include-functional arg is passed."""
    if config.getoption('--include-functional'):
        # Option provided on command line, no filtering
        return

    skip_functional = pytest.mark.skip(
        reason='--include-functional not provided')
    for item in items:
        if 'functional' in item.keywords:
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


@pytest.fixture(name='needs_sudo')
def fixture_needs_sudo():
    """Skip test if sudo command is not available."""
    if not os.path.isfile('/usr/bin/sudo'):
        pytest.skip('Needs sudo command installed.')
