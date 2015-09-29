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
import shutil
import unittest

from plinth import cfg


CONFIG_FILENAME = 'plinth.config'
TEST_CONFIG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data')
TEST_CONFIG_FILE = os.path.join(TEST_CONFIG_DIR, CONFIG_FILENAME)
SAVED_CONFIG_FILE = os.path.join(TEST_CONFIG_DIR,
                                 CONFIG_FILENAME + '.official')
CONFIG_FILE_WITH_MISSING_OPTIONS = os.path.join(TEST_CONFIG_DIR,
                                                CONFIG_FILENAME +
                                                '.with_missing_options')
CONFIG_FILE_WITH_MISSING_SECTIONS = os.path.join(TEST_CONFIG_DIR,
                                                 CONFIG_FILENAME +
                                                 '.with_missing_sections')


class CfgTestCase(unittest.TestCase):
    """Verify that the Plinth configuration module behaves as expected.

    This class deals with involving the plinth.config file in testing by
    (1) independently locating the copy of the file that the cfg module would
    find and read, then (2) copying that file to plinth/tests/data for use for
    the actual tests, and finally (3) redirecting cfg (via its
    DEFAULT_CONFIG_FILE attribute) to read that test copy.  The test copy is
    then deleted as part of the test case cleanup.
    """

    default_config_file = ''
    default_root = ''
    default_config_file_present = False
    fallback_config_file = ''
    fallback_root = ''
    fallback_config_file_present = False

    # Setup and Teardown

    @classmethod
    def setUpClass(cls):
        """Locate and copy the official plinth.config file."""
        # Save the cfg module default values
        cls.default_config_file = cfg.DEFAULT_CONFIG_FILE
        cls.default_root = cfg.DEFAULT_ROOT

        # Look for default config file
        cls.default_config_file_present =\
            os.path.isfile(cls.default_config_file)

        # Look for fallback (non-default) config file
        cls.fallback_root = os.path.realpath('.')
        cls.fallback_config_file = os.path.join(cls.fallback_root,
                                                CONFIG_FILENAME)
        cls.fallback_config_file_present =\
            os.path.isfile(cls.fallback_config_file)

        # If neither file is found...
        if not (cls.default_config_file_present or
                cls.fallback_config_file_present):
            raise FileNotFoundError('File {} could not be found.'
                                    .format(CONFIG_FILENAME))

        # Copy an official config file to the plinth/tests/data directory...
        if cls.default_config_file_present:
            shutil.copy2(cls.default_config_file, TEST_CONFIG_FILE)
        elif cls.fallback_config_file_present:
            shutil.copy2(cls.fallback_config_file, TEST_CONFIG_FILE)
        # ...and point cfg to that file as the default
        cfg.DEFAULT_CONFIG_FILE = TEST_CONFIG_FILE
        cfg.DEFAULT_ROOT = TEST_CONFIG_DIR

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests are completed."""
        # Restore the cfg module default values
        cfg.DEFAULT_CONFIG_FILE = cls.default_config_file
        cfg.DEFAULT_ROOT = cls.default_root

        # Delete the test config file(s)
        if os.path.isfile(TEST_CONFIG_FILE):
            os.remove(TEST_CONFIG_FILE)
        if os.path.isfile(SAVED_CONFIG_FILE):
            os.remove(SAVED_CONFIG_FILE)

    # Tests

    def test_read_main_menu(self):
        """Verify that the cfg.main_menu container is initially empty."""
        # Menu should be empty before...
        self.assertEqual(len(cfg.main_menu.items), 0)
        cfg.read()
        # ...and after reading the config file
        self.assertEqual(len(cfg.main_menu.items), 0)

    def test_read_default_config_file(self):
        """Verify that the default config file can be read correctly."""
        # Read the plinth.config file directly
        parser = self.read_config_file(TEST_CONFIG_FILE, TEST_CONFIG_DIR)

        # Read the plinth.config file via the cfg module
        cfg.read()

        # Compare the two results
        self.compare_configurations(parser)

    def test_read_fallback_config_file(self):
        """Verify that the fallback config file can be read correctly.

        This test will be executed only if there is a fallback (non-default)
        configuration file available for reading.  If so, the cfg default
        values for config filename and root will be temporarily modified to
        prevent any default file from being found, thus allowing the fallback
        file to be located and read.
        """
        if not self.fallback_config_file_present:
            self.skipTest('A fallback copy of {} is not available.'
                          .format(CONFIG_FILENAME))
        else:
            try:
                cfg.DEFAULT_CONFIG_FILE = '/{}'.format(CONFIG_FILENAME)
                cfg.DEFAULT_ROOT = '/'
                parser = self.read_config_file(self.fallback_config_file,
                                               self.fallback_root)
                cfg.read()
                self.compare_configurations(parser)
            finally:
                cfg.DEFAULT_CONFIG_FILE = self.default_config_file
                cfg.DEFAULT_ROOT = self.default_root

    def test_read_missing_config_file(self):
        """Verify that an exception is raised when there's no config file.

        This test will be executed only if the fallback (non-default) copy of
        plinth.config is NOT present.  If there is only a single, default
        config file available, then that file can be copied to a test area and
        be hidden by temporary renaming.  But if the default file is hidden
        and the fallback file can be found in its place, the fallback file
        will not be renamed.  Instead, the entire test will be skipped.
        """
        if self.fallback_config_file_present:
            self.skipTest(
                'Fallback copy of {} cannot be hidden to establish the test'
                'pre-condition.'.format(CONFIG_FILENAME))
        else:
            with self.assertRaises(FileNotFoundError):
                try:
                    self.rename_test_config_file()
                    cfg.read()
                finally:
                    self.restore_test_config_file()

    def test_read_config_file_with_missing_sections(self):
        """Verify that missing configuration sections can be detected."""
        self.assertRaises(configparser.NoSectionError,
                          self.read_temp_config_file,
                          CONFIG_FILE_WITH_MISSING_SECTIONS)

    def test_read_config_file_with_missing_options(self):
        """Verify that missing configuration options can be detected."""
        self.assertRaises(configparser.NoOptionError,
                          self.read_temp_config_file,
                          CONFIG_FILE_WITH_MISSING_OPTIONS)

    # Helper Methods

    def read_config_file(self, config_file, root):
        """Read the specified configuration file independently from cfg.py."""
        parser = configparser.ConfigParser(defaults={'root': root})
        parser.read(config_file)
        return parser

    def compare_configurations(self, parser):
        """Compare two sets of configuration values."""
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
        self.assertIsInstance(cfg.use_x_forwarded_host, bool)
        self.assertEqual(parser.get('Network', 'use_x_forwarded_host'),
                         str(cfg.use_x_forwarded_host))
        self.assertEqual(parser.get('Misc', 'danube_edition'),
                         str(cfg.danube_edition))

    def read_temp_config_file(self, test_file):
        """Read the specified test configuration file."""
        self.replace_test_config_file(test_file)
        try:
            cfg.read()
        finally:
            self.restore_test_config_file()

    def rename_test_config_file(self):
        """Rename the test config file so that it can't be read."""
        shutil.move(TEST_CONFIG_FILE, SAVED_CONFIG_FILE)

    def replace_test_config_file(self, test_file):
        """Replace plinth.config with the specified temporary config file."""
        self.rename_test_config_file()
        shutil.copy2(test_file, TEST_CONFIG_FILE)

    def restore_test_config_file(self):
        """Restore the test plinth.config file."""
        if os.path.isfile(TEST_CONFIG_FILE):
            os.remove(TEST_CONFIG_FILE)
        shutil.move(SAVED_CONFIG_FILE, TEST_CONFIG_FILE)
