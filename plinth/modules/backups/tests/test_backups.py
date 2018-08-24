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

import collections
import unittest
from unittest.mock import patch

from plinth.module_loader import load_modules
from ..backups import _list_of_all_apps_for_backup, _get_apps_in_order, \
    Packet, validate, _shutdown_services, _restore_services


def _get_test_manifest(name):
    return validate({
        'config': {
            'directories': ['/etc/' + name + '/config.d/'],
            'files': ['/etc/' + name + '/config'],
        },
        'data': {
            'directories': ['/var/lib/' + name + '/data.d/'],
            'files': ['/var/lib/' + name + '/data'],
        },
        'secrets': {
            'directories': ['/etc/' + name + '/secrets.d/'],
            'files': ['/etc/' + name + '/secrets'],
        },
        'services': [name]
    })


class TestBackups(unittest.TestCase):
    """Test cases for backups module."""

    def test_packet_process_manifests(self):
        """Test that directories/files are collected from manifests."""
        manifests = [
            ('a', None, _get_test_manifest('a')),
            ('b', None, _get_test_manifest('b')),
        ]
        packet = Packet('backup', 'apps', '/', manifests)
        for manifest in manifests:
            backup = manifest[2]
            for x in ['config', 'data', 'secrets']:
                for d in backup[x]['directories']:
                    assert d in packet.directories
                for f in backup[x]['files']:
                    assert f in packet.files

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

    def test__shutdown_services(self):
        """Test that services are stopped in correct order."""
        manifests = [
            ('a', None, _get_test_manifest('a')),
            ('b', None, _get_test_manifest('b')),
        ]
        state = _shutdown_services(manifests)
        assert 'a' in state
        assert 'b' in state

    @patch('plinth.actions.superuser_run')
    def test__restore_services(self, run):
        """Test that services are restored in correct order."""
        original_state = collections.OrderedDict()
        original_state['a'] = {
            'app_name': 'a', 'app': None, 'was_running': True}
        original_state['b'] = {
            'app_name': 'b', 'app': None, 'was_running': False}
        _restore_services(original_state)
        run.assert_called_once_with('service', ['start', 'a'])
