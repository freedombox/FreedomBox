# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for backups module API.
"""

from unittest.mock import MagicMock, call, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from plinth.app import App

from .. import api, forms, repository
from ..components import BackupRestore

# pylint: disable=protected-access
pytestmark = pytest.mark.django_db


def _get_test_manifest(name):
    return {
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
        'services': [name, {
            'type': 'apache',
            'name': name,
            'kind': 'site'
        }]
    }


def _get_backup_component(name):
    """Return a BackupRestore component."""
    return BackupRestore(name, **_get_test_manifest(name))


class AppTest(App):
    """Sample App for testing."""
    app_id = 'test-app'


def _get_test_app(name):
    """Return an App."""
    app = AppTest()
    app.app_id = name
    app._all_apps[name] = app
    app.add(_get_backup_component(name + '-component'))
    return app


@pytest.mark.usefixtures('load_cfg')
class TestBackupProcesses:
    """Test cases for backup processes"""

    @staticmethod
    def test_packet_init():
        """Test that packet is initialized properly."""
        packet = api.Packet('backup', 'apps', '/', [])
        assert packet.archive_comment is None
        packet = api.Packet('backup', 'apps', '/', [],
                            archive_comment='test comment')
        assert packet.archive_comment == 'test comment'

    @staticmethod
    def test_packet_collected_files_directories():
        """Test that directories/files are collected from manifests."""
        components = [_get_backup_component('a'), _get_backup_component('b')]
        packet = api.Packet('backup', 'apps', '/', components,
                            archive_comment='test comment')
        for component in components:
            for section in ['config', 'data', 'secrets']:
                for directory in getattr(component, section)['directories']:
                    assert directory in packet.directories
                for file_path in getattr(component, section)['files']:
                    assert file_path in packet.files

    @staticmethod
    def test_backup_apps():
        """Test that backup_handler is called."""
        backup_handler = MagicMock()
        api.backup_apps(backup_handler,
                        path=repository.RootBorgRepository.PATH)
        backup_handler.assert_called_once()

    @staticmethod
    @patch('plinth.modules.backups.api._install_apps_before_restore')
    def test_restore_apps(mock_install):
        """Test that restore_handler is called."""
        restore_handler = MagicMock()
        api.restore_apps(restore_handler)
        restore_handler.assert_called_once()

    @staticmethod
    @patch('plinth.app.App.get_setup_state')
    @patch('plinth.app.App.list')
    def test_get_all_components_for_backup(apps_list, get_setup_state):
        """Test listing components supporting backup and needing backup."""
        get_setup_state.side_effect = [
            App.SetupState.UP_TO_DATE,
            App.SetupState.NEEDS_SETUP,
            App.SetupState.UP_TO_DATE,
        ]
        apps = [_get_test_app('a'), _get_test_app('b'), _get_test_app('c')]
        apps_list.return_value = apps

        returned_components = api.get_all_components_for_backup()
        expected_components = [
            apps[0].components['a-component'],
            apps[2].components['c-component']
        ]
        assert returned_components == expected_components

    @staticmethod
    @patch('plinth.app.App.list')
    def test_get_components_in_order(apps_list):
        """Test that components are listed in correct dependency order."""
        apps = [
            _get_test_app('names'),
            _get_test_app('other'),
            _get_test_app('config')
        ]
        apps_list.return_value = apps

        app_ids = ['config', 'names']
        components = api.get_components_in_order(app_ids)
        assert len(components) == 2
        assert components[0].app_id == 'names'
        assert components[1].app_id == 'config'

    @staticmethod
    def test__lockdown_apps():
        """Test that locked flag is set for each app."""
        apps = [_get_test_app('test-app-1'), _get_test_app('test-app-2')]
        components = [
            apps[0].components['test-app-1-component'],
            apps[1].components['test-app-2-component']
        ]

        api._lockdown_apps(components, True)
        assert apps[0].locked
        assert apps[1].locked

        api._lockdown_apps(components, False)
        assert not apps[0].locked
        assert not apps[1].locked

    @staticmethod
    @patch('plinth.action_utils.webserver_is_enabled')
    @patch('plinth.action_utils.service_is_running')
    @patch('plinth.privileged.service.stop')
    @patch('plinth.modules.apache.privileged.disable')
    def test__shutdown_services(apache_disable, service_stop,
                                service_is_running, webserver_is_enabled):
        """Test that services are stopped in correct order."""
        components = [_get_backup_component('a'), _get_backup_component('b')]
        service_is_running.return_value = True
        webserver_is_enabled.return_value = True
        state = api._shutdown_services(components)

        expected_state = [
            api.ServiceHandler.create(components[0],
                                      components[0].services[0]),
            api.ServiceHandler.create(components[0],
                                      components[0].services[1]),
            api.ServiceHandler.create(components[1],
                                      components[1].services[0]),
            api.ServiceHandler.create(components[1],
                                      components[1].services[1]),
        ]
        assert state == expected_state

        service_is_running.assert_has_calls([call('b'), call('a')])
        webserver_is_enabled.assert_has_calls(
            [call('b', kind='site'),
             call('a', kind='site')])

        apache_disable.assert_has_calls([call('b', 'site'), call('a', 'site')])
        service_stop.assert_has_calls([call('b'), call('a')])

    @staticmethod
    @patch('plinth.privileged.service.start')
    @patch('plinth.modules.apache.privileged.enable')
    def test__restore_services(apache_enable, service_start):
        """Test that services are restored in correct order."""
        original_state = [
            api.SystemServiceHandler(None, 'a-service'),
            api.SystemServiceHandler(None, 'b-service'),
            api.ApacheServiceHandler(None, {
                'name': 'c-service',
                'kind': 'site'
            }),
            api.ApacheServiceHandler(None, {
                'name': 'd-service',
                'kind': 'site'
            })
        ]
        original_state[0].was_running = True
        original_state[1].was_running = False
        original_state[2].was_enabled = True
        original_state[3].was_enabled = False
        api._restore_services(original_state)
        service_start.assert_has_calls([call('a-service')])
        apache_enable.assert_has_calls([call('c-service', 'site')])

    @staticmethod
    def test__run_operation():
        """Test that operation runs handler and app hooks."""
        components = [_get_backup_component('a'), _get_backup_component('b')]
        packet = api.Packet('backup', 'apps', '/', components)
        packet.components[0].backup_pre = MagicMock()
        packet.components[0].backup_post = MagicMock()
        packet.components[1].backup_pre = MagicMock()
        packet.components[1].backup_post = MagicMock()
        handler = MagicMock()
        api._run_operation(handler, packet)
        handler.assert_has_calls([call(packet, encryption_passphrase=None)])

        calls = [call(packet)]
        packet.components[0].backup_pre.assert_has_calls(calls)
        packet.components[0].backup_post.assert_has_calls(calls)
        packet.components[1].backup_pre.assert_has_calls(calls)
        packet.components[1].backup_post.assert_has_calls(calls)


class TestBackupModule:
    """Tests of the backups django module, like views or forms."""

    @staticmethod
    def test_file_upload():
        # posting a video should fail
        video_file = SimpleUploadedFile("video.mp4", b"file_content",
                                        content_type="video/mp4")
        form = forms.UploadForm({}, {'file': video_file})
        assert not form.is_valid()

        # posting an archive file should work
        archive_file = SimpleUploadedFile("backup.tar.gz", b"file_content",
                                          content_type="application/gzip")
        form = forms.UploadForm({}, {'file': archive_file})
        form.is_valid()
        assert form.is_valid()
