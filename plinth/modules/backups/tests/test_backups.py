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
Tests for backups module.
"""

import unittest

from plinth.module_loader import load_modules
from ..backups import _list_of_all_apps_for_backup, _get_apps_in_order


class TestBackups(unittest.TestCase):
    """Test cases for backups module."""

    def test__list_of_all_apps_for_backups(self):
        """Test that apps supporting backup are included in returned list."""
        load_modules()
        apps = _list_of_all_apps_for_backup()
        assert isinstance(apps, list)
        # apps may be empty, if no apps supporting backup are installed.

    def test__get_apps_in_order(self):
        """Test that apps are listed in correct dependency order."""
        load_modules()
        app_names = ['config', 'names']
        apps = _get_apps_in_order(app_names)
        ordered_app_names = [x[0] for x in apps]

        names_index = ordered_app_names.index('names')
        config_index = ordered_app_names.index('config')
        assert names_index < config_index
