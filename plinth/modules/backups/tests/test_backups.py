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
from unittest.mock import call, patch, MagicMock

from plinth.module_loader import load_modules
from ..backups import validate, Packet, backup_apps, restore_apps, \
    get_all_apps_for_backup, _get_apps_in_order, _get_manifests, \
    _lockdown_apps, _shutdown_services, _restore_services


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

    def test_backup_apps(self):
        """Test that backup_handler is called."""
        backup_handler = MagicMock()
        backup_apps(backup_handler)
        backup_handler.assert_called_once()

    def test_restore_apps(self):
        """Test that restore_handler is called."""
        restore_handler = MagicMock()
        restore_apps(restore_handler)
        restore_handler.assert_called_once()

    def test_get_all_apps_for_backups(self):
        """Test that apps supporting backup are included in returned list."""
        load_modules()
        apps = get_all_apps_for_backup()
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

    def test__get_manifests(self):
        """Test that manifests are collected from the apps."""
        a = MagicMock(backup=_get_test_manifest('a'))
        b = MagicMock(backup=_get_test_manifest('b'))
        apps = [
            ('a', a),
            ('b', b),
        ]
        manifests = _get_manifests(apps)
        assert ('a', a, a.backup) in manifests
        assert ('b', b, b.backup) in manifests

    def test__lockdown_apps(self):
        """Test that locked flag is set for each app."""
        a = MagicMock(locked=False)
        b = MagicMock(locked=None)
        apps = [
            ('a', a),
            ('b', b),
        ]
        _lockdown_apps(apps, True)
        assert a.locked is True
        assert b.locked is True

    @patch('plinth.action_utils.service_is_running')
    @patch('plinth.actions.superuser_run')
    def test__shutdown_services(self, run, is_running):
        """Test that services are stopped in correct order."""
        manifests = [
            ('a', None, _get_test_manifest('a')),
            ('b', None, _get_test_manifest('b')),
        ]
        is_running.return_value = True
        state = _shutdown_services(manifests)
        assert 'a' in state
        assert 'b' in state
        is_running.assert_any_call('a')
        is_running.assert_any_call('b')
        calls = [
            call('service', ['stop', 'b']),
            call('service', ['stop', 'a'])
        ]
        run.assert_has_calls(calls)

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
