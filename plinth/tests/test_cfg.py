# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for configuration module.
"""

import configparser
import logging
import os
from unittest.mock import patch

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


def test_read_default_config_file():
    """Verify that the default config file can be read correctly."""
    config_file, config_dir = cfg.get_fallback_config_paths()

    # Read the plinth.config file directly
    parser = configparser.ConfigParser(defaults={'root': config_dir})
    parser.read(config_file)

    # Read the plinth.config file via the cfg module
    cfg.read(config_file, config_dir)

    # Compare the two results
    compare_configurations(parser)


@patch('plinth.cfg.get_config_paths')
def test_read_primary_config_file(get_config_paths):
    """Verify that the primary config file is used by default."""
    expected_config_path = CONFIG_FILE_WITH_MISSING_OPTIONS
    root_directory = 'x-default-root'
    expected_root_directory = os.path.realpath(root_directory)
    get_config_paths.return_value = (expected_config_path, root_directory)

    cfg.read()

    assert cfg.config_file == expected_config_path
    assert cfg.root == expected_root_directory


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
    cfg.read('x-non-existant-file', 'x-root-directory')


def test_read_config_file_with_missing_sections():
    """Verify that missing configuration sections can be detected."""
    cfg.read(CONFIG_FILE_WITH_MISSING_SECTIONS, TEST_CONFIG_DIR)
    assert cfg.box_name == 'FreedomBoxTestMissingSections'


def test_read_config_file_with_missing_options():
    """Verify that missing configuration options can be detected."""
    cfg.read(CONFIG_FILE_WITH_MISSING_OPTIONS, TEST_CONFIG_DIR)
    assert cfg.box_name == 'FreedomBoxTestMissingOptions'


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
