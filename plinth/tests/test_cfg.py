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

import configparser
import os
import shutil
import unittest

from plinth import cfg


CONFIG_FILENAME = 'plinth.config'
SAVED_CONFIG_FILE = CONFIG_FILENAME + '.official'
CONFIG_FILE_WITH_MISSING_OPTIONS = CONFIG_FILENAME +\
    '.with_missing_options'
CONFIG_FILE_WITH_MISSING_SECTIONS = CONFIG_FILENAME +\
    '.with_missing_sections'


class CfgTestCase(unittest.TestCase):
    """Verify that the Plinth configuration module behaves as expected."""

    config_file = ''
    directory = ''

    @classmethod
    def setUpClass(cls):
        """Locate the official plinth.config file."""
        if os.path.isfile(cfg.DEFAULT_CONFIG_FILE):
            cls.config_file = cfg.DEFAULT_CONFIG_FILE
            cls.directory = cfg.DEFAULT_ROOT
        else:
            cls.directory = os.path.realpath('.')
            cls.config_file = os.path.join(cls.directory,
                                           CONFIG_FILENAME)
            if not(os.path.isfile(cls.config_file)):
                raise FileNotFoundError('File {} could not be found.',
                                        format(CONFIG_FILENAME))

    # Tests
    def test_read_main_menu(self):
        """Verify that the cfg.main_menu container is initially empty."""
        # Menu should be empty before...
        self.assertEqual(len(cfg.main_menu.items), 0)
        cfg.read()
        # ...and after reading the config file
        self.assertEqual(len(cfg.main_menu.items), 0)

    def test_read_official_config_file(self):
        """Verify that the plinth.config file can be read correctly."""
        # Read the plinth.config file directly
        parser = self.read_config_file(self.config_file)

        # Read the plinth.config file via the cfg module
        cfg.read()

        # Compare the two sets of configuration values.
        # Note that the count of items within each section includes the number
        # of default items (1, for 'root').
        self.assertEqual(3, len(parser.items('Name')))
        self.assertEqual(parser.get('Name', 'product_name'), cfg.product_name)
        self.assertEqual(parser.get('Name', 'box_name'), cfg.box_name)

        self.assertEqual(13, len(parser.items('Path')))
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
        self.assertEqual(parser.get('Path', 'pidfile'), cfg.pidfile)

        self.assertEqual(5, len(parser.items('Network')))
        self.assertEqual(parser.get('Network', 'host'), cfg.host)
        self.assertEqual(int(parser.get('Network', 'port')), cfg.port)
        self.assertEqual(parser.get('Network', 'secure_proxy_ssl_header'),
                         cfg.secure_proxy_ssl_header)
        self.assertEqual(parser.get('Network', 'use_x_forwarded_host'),
                         cfg.use_x_forwarded_host)

    def test_read_missing_config_file(self):
        """Verify that an exception is raised when there's no config file."""
        with self.assertRaises(FileNotFoundError):
            try:
                self.rename_official_config_file()
                cfg.read()
            finally:
                self.restore_official_config_file()

    def test_read_config_file_with_missing_sections(self):
        """Verify that missing configuration sections can be detected."""
        self.assertRaises(configparser.NoSectionError,
                          self.read_test_config_file,
                          CONFIG_FILE_WITH_MISSING_SECTIONS)

    def test_read_config_file_with_missing_options(self):
        """Verify that missing configuration options can be detected."""
        self.assertRaises(configparser.NoOptionError,
                          self.read_test_config_file,
                          CONFIG_FILE_WITH_MISSING_OPTIONS)

    # Helper Methods

    def read_config_file(self, file):
        """Read the configuration file independently from cfg.py."""
        parser = configparser.ConfigParser(
            defaults={'root': self.directory})
        parser.read(file)
        return parser

    def read_test_config_file(self, test_file):
        """Read the specified test configuration file."""
        self.replace_official_config_file(test_file)
        try:
            cfg.read()
        finally:
            self.restore_official_config_file()

    def rename_official_config_file(self):
        """Rename the official config file so that it can't be read."""
        shutil.move(self.config_file,
                    os.path.join(self.directory, SAVED_CONFIG_FILE))

    def replace_official_config_file(self, test_file):
        """Replace plinth.config with the specified test config file."""
        self.rename_official_config_file()
        test_data_directory = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'data')
        shutil.copy2(os.path.join(test_data_directory, test_file),
                     self.config_file)

    def restore_official_config_file(self):
        """Restore the official plinth.config file."""
        if os.path.isfile(self.config_file):
            os.remove(self.config_file)
        shutil.move(os.path.join(self.directory, SAVED_CONFIG_FILE),
                    self.config_file)


if __name__ == '__main__':
    unittest.main()
