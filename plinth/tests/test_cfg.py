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
Test module for configuration module.
"""

import configparser
import logging
import os

import pytest

from plinth import cfg

TEST_CONFIG_DIR = \
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
CONFIG_FILE_WITH_MISSING_OPTIONS = \
    os.path.join(TEST_CONFIG_DIR, 'plinth.config.with_missing_options')
CONFIG_FILE_WITH_MISSING_SECTIONS = \
    os.path.join(TEST_CONFIG_DIR, 'plinth.config.with_missing_sections')

logging.disable(logging.CRITICAL)

pytestmark = pytest.mark.usefixtures('load_cfg')


@pytest.fixture(name='test_config_file')
def fixture_test_config_file(load_cfg):
    """Test fixture to return the configuration file path"""
    return cfg.get_config_paths()[0]


@pytest.fixture(name='test_config_dir')
def fixture_test_config_dir(load_cfg):
    """Test fixture to return the configuration file directory."""
    return cfg.get_config_paths()[1]


def test_read_default_config_file(test_config_dir, test_config_file):
    """Verify that the default config file can be read correctly."""
    # Read the plinth.config file directly
    parser = configparser.ConfigParser(defaults={'root': test_config_dir})
    parser.read(test_config_file)

    # Read the plinth.config file via the cfg module
    cfg.read(test_config_file, test_config_dir)

    # Compare the two results
    compare_configurations(parser)


def test_read_primary_config_file():
    """Verify that the primary config file is used by default."""
    original_config_path = cfg.DEFAULT_CONFIG_FILE
    original_root_directory = cfg.DEFAULT_ROOT

    expected_config_path = CONFIG_FILE_WITH_MISSING_OPTIONS
    root_directory = 'x-default-root'
    expected_root_directory = os.path.realpath(root_directory)

    try:
        cfg.DEFAULT_CONFIG_FILE = expected_config_path
        cfg.DEFAULT_ROOT = root_directory
        # reading the config file will fail, but still cfg.root and
        # cfg.config_file will be set for parsing the config file
        try:
            cfg.read()
        except configparser.NoOptionError:
            pass
        assert cfg.config_file == expected_config_path
        assert cfg.root == expected_root_directory
    finally:
        cfg.DEFAULT_CONFIG_FILE = original_config_path
        cfg.DEFAULT_ROOT = original_root_directory


def test_read_fallback_config_file():
    """Verify that the correct fallback config file is used"""
    test_dir = os.path.dirname(os.path.realpath(__file__))
    fallback_root = os.path.realpath(os.path.join(test_dir, '..', '..'))
    fallback_config_file = os.path.join(fallback_root, 'plinth.config')
    config_path, root_directory = cfg.get_fallback_config_paths()
    cfg.read(config_path, root_directory)
    assert cfg.config_file == fallback_config_file
    assert cfg.root == fallback_root


def test_read_missing_config_file():
    """Verify that an exception is raised when there's no config file."""
    with pytest.raises(FileNotFoundError):
        cfg.read('x-non-existant-file', 'x-root-directory')


def test_read_config_file_with_missing_sections(test_config_dir):
    """Verify that missing configuration sections can be detected."""
    with pytest.raises(configparser.NoSectionError):
        cfg.read(CONFIG_FILE_WITH_MISSING_SECTIONS, test_config_dir)


def test_read_config_file_with_missing_options(test_config_dir):
    """Verify that missing configuration options can be detected."""
    with pytest.raises(configparser.NoOptionError):
        cfg.read(CONFIG_FILE_WITH_MISSING_OPTIONS, test_config_dir)


def compare_configurations(parser):
    """Compare two sets of configuration values."""
    # Note that the count of items within each section includes the number
    # of default items (1, for 'root').
    assert len(parser.items('Path')) == 9
    assert parser.get('Path', 'root') == cfg.root
    assert parser.get('Path', 'file_root') == cfg.file_root
    assert parser.get('Path', 'config_dir') == cfg.config_dir
    assert parser.get('Path', 'custom_static_dir') == cfg.custom_static_dir
    assert parser.get('Path', 'data_dir') == cfg.data_dir
    assert parser.get('Path', 'store_file') == cfg.store_file
    assert parser.get('Path', 'actions_dir') == cfg.actions_dir
    assert parser.get('Path', 'doc_dir') == cfg.doc_dir

    assert len(parser.items('Network')) == 6
    assert parser.get('Network', 'host') == cfg.host
    assert int(parser.get('Network', 'port')) == cfg.port
    assert parser.get('Network', 'secure_proxy_ssl_header') == \
        cfg.secure_proxy_ssl_header
    assert isinstance(cfg.use_x_forwarded_for, bool)
    assert parser.get('Network', 'use_x_forwarded_for') == \
        str(cfg.use_x_forwarded_for)
    assert isinstance(cfg.use_x_forwarded_host, bool)
    assert parser.get('Network', 'use_x_forwarded_host') == \
        str(cfg.use_x_forwarded_host)
    assert len(parser.items('Misc')) == 2
    assert parser.get('Misc', 'box_name') == cfg.box_name
