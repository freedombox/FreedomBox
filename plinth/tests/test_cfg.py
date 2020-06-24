# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for configuration module.
"""

import configparser
import logging
import os
import pathlib
from unittest.mock import patch

import pytest

from plinth import cfg

TEST_CONFIG_DIR = \
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 'data', 'configs')
CONFIG_FILE_WITH_MISSING_OPTIONS = \
    os.path.join(TEST_CONFIG_DIR, 'freedombox.config.with_missing_options')
CONFIG_FILE_WITH_MISSING_SECTIONS = \
    os.path.join(TEST_CONFIG_DIR, 'freedombox.config.with_missing_sections')

logging.disable(logging.CRITICAL)

pytestmark = pytest.mark.usefixtures('load_cfg')


def test_read_default_config_file():
    """Verify that the default config file can be read correctly."""
    config_file = cfg.get_develop_config_path()

    # Read the freedombox.config file directly
    parser = configparser.ConfigParser(
        defaults={
            'parent_dir': pathlib.Path(config_file).parent,
            'parent_parent_dir': pathlib.Path(config_file).parent.parent
        })
    parser.read(config_file)

    # Read the freedombox.config file via the cfg module
    cfg.read_file(config_file)

    # Compare the two results
    compare_configurations(parser)


@patch('plinth.cfg.get_config_path')
def test_read_primary_config_file(get_config_path):
    """Verify that the primary config file is used by default."""
    config_path = CONFIG_FILE_WITH_MISSING_OPTIONS
    get_config_path.return_value = config_path
    cfg.read()
    assert cfg.config_files[-1] == config_path


def test_read_develop_config_file():
    """Verify that the correct develop config file is used."""
    test_dir = os.path.dirname(os.path.realpath(__file__))
    develop_root = os.path.realpath(os.path.join(test_dir, '..', '..'))
    develop_config_file = os.path.join(develop_root, 'plinth',
                                       'develop.config')
    config_path = cfg.get_develop_config_path()
    cfg.read_file(config_path)
    assert cfg.config_files[-1] == develop_config_file
    assert cfg.file_root == develop_root


def test_read_missing_config_file():
    """Verify that an exception is raised when there's no config file."""
    cfg.read_file('x-non-existant-file')


def test_read_config_file_with_missing_sections():
    """Verify that missing configuration sections can be detected."""
    cfg.read_file(CONFIG_FILE_WITH_MISSING_SECTIONS)
    assert cfg.box_name == 'FreedomBoxTestMissingSections'


def test_read_config_file_with_missing_options():
    """Verify that missing configuration options can be detected."""
    cfg.read_file(CONFIG_FILE_WITH_MISSING_OPTIONS)
    assert cfg.box_name == 'FreedomBoxTestMissingOptions'


def compare_configurations(parser):
    """Compare two sets of configuration values."""
    assert parser.get('Path', 'file_root') == cfg.file_root
    assert parser.get('Path', 'config_dir') == cfg.config_dir
    assert parser.get('Path', 'custom_static_dir') == cfg.custom_static_dir
    assert parser.get('Path', 'data_dir') == cfg.data_dir
    assert parser.get('Path', 'store_file') == cfg.store_file
    assert parser.get('Path', 'actions_dir') == cfg.actions_dir
    assert parser.get('Path', 'doc_dir') == cfg.doc_dir

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

    assert parser.get('Misc', 'box_name') == cfg.box_name
