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
Test module for configuration module.
"""

import configparser
import os
import unittest

from plinth import cfg


TEST_CONFIG_DIR = \
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
CONFIG_FILE_WITH_MISSING_OPTIONS = \
    os.path.join(TEST_CONFIG_DIR, 'plinth.config.with_missing_options')
CONFIG_FILE_WITH_MISSING_SECTIONS = \
    os.path.join(TEST_CONFIG_DIR, 'plinth.config.with_missing_sections')


class TestCfg(unittest.TestCase):
    """Verify that the Plinth configuration module behaves as expected."""
    @classmethod
    def setUpClass(cls):
        """Locate and copy the official plinth.config file."""
        cls.test_config_file, cls.test_config_dir = cfg.get_config_file()

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests are completed."""
        cfg.read()

    def test_read_default_config_file(self):
        """Verify that the default config file can be read correctly."""
        # Read the plinth.config file directly
        parser = configparser.ConfigParser(
            defaults={'root': self.test_config_dir})
        parser.read(self.test_config_file)

        # Read the plinth.config file via the cfg module
        cfg.read(self.test_config_file, self.test_config_dir)

        # Compare the two results
        self.compare_configurations(parser)

    def test_read_primary_config_file(self):
        """Verify that the primary config file can be read correctly."""
        original_file_path = cfg.DEFAULT_CONFIG_FILE
        original_root_directory = cfg.DEFAULT_ROOT

        expected_file_path = CONFIG_FILE_WITH_MISSING_OPTIONS
        expected_root_directory = 'x-default-root'

        try:
            cfg.DEFAULT_CONFIG_FILE = expected_file_path
            cfg.DEFAULT_ROOT = expected_root_directory
            file_path, root_directoy = cfg.get_config_file()
            self.assertEqual(file_path, expected_file_path)
            self.assertEqual(root_directoy, expected_root_directory)
        finally:
            cfg.DEFAULT_CONFIG_FILE = original_file_path
            cfg.DEFAULT_ROOT = original_root_directory

    def test_read_fallback_config_file(self):
        """Verify that the fallback config file can be read correctly."""
        original_file_path = cfg.DEFAULT_CONFIG_FILE
        original_root_directory = cfg.DEFAULT_ROOT

        fallback_root = os.path.realpath('.')
        fallback_config_file = os.path.join(fallback_root, 'plinth.config')
        expected_file_path = os.path.realpath(fallback_config_file)
        expected_root_directory = fallback_root

        try:
            cfg.DEFAULT_CONFIG_FILE = 'x-non-existant-file'
            cfg.DEFAULT_ROOT = 'x-non-existant-directory'
            file_path, root_directoy = cfg.get_config_file()
            self.assertEqual(file_path, expected_file_path)
            self.assertEqual(root_directoy, expected_root_directory)
        finally:
            cfg.DEFAULT_CONFIG_FILE = original_file_path
            cfg.DEFAULT_ROOT = original_root_directory

    def test_read_missing_config_file(self):
        """Verify that an exception is raised when there's no config file."""
        self.assertRaises(FileNotFoundError, cfg.read, 'x-non-existant-file',
                          'x-root-directory')

    def test_read_config_file_with_missing_sections(self):
        """Verify that missing configuration sections can be detected."""
        self.assertRaises(
            configparser.NoSectionError, cfg.read,
            CONFIG_FILE_WITH_MISSING_SECTIONS, self.test_config_dir)

    def test_read_config_file_with_missing_options(self):
        """Verify that missing configuration options can be detected."""
        self.assertRaises(
            configparser.NoOptionError, cfg.read,
            CONFIG_FILE_WITH_MISSING_OPTIONS, self.test_config_dir)

    def compare_configurations(self, parser):
        """Compare two sets of configuration values."""
        # Note that the count of items within each section includes the number
        # of default items (1, for 'root').
        self.assertEqual(11, len(parser.items('Path')))
        self.assertEqual(parser.get('Path', 'root'), cfg.root)
        self.assertEqual(parser.get('Path', 'file_root'), cfg.file_root)
        self.assertEqual(parser.get('Path', 'config_dir'), cfg.config_dir)
        self.assertEqual(parser.get('Path', 'data_dir'), cfg.data_dir)
        self.assertEqual(parser.get('Path', 'store_file'), cfg.store_file)
        self.assertEqual(parser.get('Path', 'actions_dir'),
                         cfg.actions_dir)
        self.assertEqual(parser.get('Path', 'doc_dir'), cfg.doc_dir)
        self.assertEqual(parser.get('Path', 'status_log_file'),
                         cfg.status_log_file)
        self.assertEqual(parser.get('Path', 'access_log_file'),
                         cfg.access_log_file)

        self.assertEqual(5, len(parser.items('Network')))
        self.assertEqual(parser.get('Network', 'host'), cfg.host)
        self.assertEqual(int(parser.get('Network', 'port')), cfg.port)
        self.assertEqual(parser.get('Network', 'secure_proxy_ssl_header'),
                         cfg.secure_proxy_ssl_header)
        self.assertIsInstance(cfg.use_x_forwarded_host, bool)
        self.assertEqual(parser.get('Network', 'use_x_forwarded_host'),
                         str(cfg.use_x_forwarded_host))
        self.assertEqual(3, len(parser.items('Misc')))
        self.assertEqual(parser.get('Misc', 'danube_edition'),
                         str(cfg.danube_edition))
        self.assertEqual(parser.get('Misc', 'box_name'), cfg.box_name)
