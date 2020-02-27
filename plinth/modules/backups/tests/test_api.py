# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for backups module API.
"""

from unittest.mock import MagicMock, call, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from .. import api, forms, repository

# pylint: disable=protected-access


def _get_test_manifest(name):
    return api.validate({
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
    })


def _get_backup_app(name):
    """Return a dummy BackupApp object."""
    return api.BackupApp(name, MagicMock(backup=_get_test_manifest(name)))


class TestBackupApp:
    """Test the BackupApp class."""
    @staticmethod
    def test_run_hook():
        """Test running a hook on an application."""
        packet = api.Packet('backup', 'apps', '/', [])
        hook = 'testhook_pre'
        app = MagicMock()
        backup_app = api.BackupApp('app_name', app)
        backup_app.run_hook(hook, packet)

        app.testhook_pre.assert_has_calls([call(packet)])
        assert not packet.errors

        app.testhook_pre.reset_mock()
        app.testhook_pre.side_effect = Exception()
        backup_app.run_hook(hook, packet)
        assert packet.errors == [api.BackupError('hook', app, hook=hook)]

        del app.testhook_pre
        backup_app.run_hook(hook, packet)


@pytest.mark.usefixtures('load_cfg')
class TestBackupProcesses:
    """Test cases for backup processes"""
    @staticmethod
    def test_packet_process_manifests():
        """Test that directories/files are collected from manifests."""
        apps = [_get_backup_app('a'), _get_backup_app('b')]
        packet = api.Packet('backup', 'apps', '/', apps)
        for app in apps:
            for section in ['config', 'data', 'secrets']:
                for directory in app.manifest[section]['directories']:
                    assert directory in packet.directories
                for file_path in app.manifest[section]['files']:
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
    @patch('plinth.module_loader.loaded_modules.items')
    def test_restore_apps(mock_install, modules):
        """Test that restore_handler is called."""
        modules.return_value = [('a', MagicMock())]
        restore_handler = MagicMock()
        api.restore_apps(restore_handler)
        restore_handler.assert_called_once()

    @staticmethod
    @patch('plinth.module_loader.loaded_modules.items')
    def test_get_all_apps_for_backup(modules):
        """Test listing apps supporting backup and needing backup."""
        apps = [
            ('a', MagicMock(backup=_get_test_manifest('a'))),
            ('b', MagicMock(backup=_get_test_manifest('b'))),
            ('c', MagicMock(backup=None)),
            ('d', MagicMock()),
        ]
        del apps[3][1].backup
        modules.return_value = apps

        returned_apps = api.get_all_apps_for_backup()
        expected_apps = [
            api.BackupApp('a', apps[0][1]),
            api.BackupApp('b', apps[1][1]),
            api.BackupApp('c', apps[2][1])
        ]
        assert returned_apps == expected_apps

    @staticmethod
    @patch('plinth.module_loader.loaded_modules.items')
    def test_get_apps_in_order(modules):
        """Test that apps are listed in correct dependency order."""
        apps = [
            ('names', MagicMock(backup=_get_test_manifest('names'))),
            ('config', MagicMock(backup=_get_test_manifest('config'))),
        ]
        modules.return_value = apps

        app_names = ['config', 'names']
        apps = api.get_apps_in_order(app_names)
        assert apps[0].name == 'names'
        assert apps[1].name == 'config'

    @staticmethod
    def test__lockdown_apps():
        """Test that locked flag is set for each app."""
        app_a = MagicMock(locked=False)
        app_b = MagicMock(locked=None)
        apps = [MagicMock(app=app_a), MagicMock(app=app_b)]
        api._lockdown_apps(apps, True)
        assert app_a.locked is True
        assert app_b.locked is True

    @staticmethod
    @patch('plinth.action_utils.webserver_is_enabled')
    @patch('plinth.action_utils.service_is_running')
    @patch('plinth.actions.superuser_run')
    def test__shutdown_services(run, service_is_running, webserver_is_enabled):
        """Test that services are stopped in correct order."""
        apps = [_get_backup_app('a'), _get_backup_app('b')]
        service_is_running.return_value = True
        webserver_is_enabled.return_value = True
        state = api._shutdown_services(apps)

        expected_state = [
            api.ServiceHandler.create(apps[0],
                                      apps[0].manifest['services'][0]),
            api.ServiceHandler.create(apps[0],
                                      apps[0].manifest['services'][1]),
            api.ServiceHandler.create(apps[1],
                                      apps[1].manifest['services'][0]),
            api.ServiceHandler.create(apps[1], apps[1].manifest['services'][1])
        ]
        assert state == expected_state

        service_is_running.assert_has_calls([call('b'), call('a')])
        webserver_is_enabled.assert_has_calls(
            [call('b', kind='site'),
             call('a', kind='site')])

        calls = [
            call('apache', ['disable', '--name', 'b', '--kind', 'site']),
            call('service', ['stop', 'b']),
            call('apache', ['disable', '--name', 'a', '--kind', 'site']),
            call('service', ['stop', 'a'])
        ]
        run.assert_has_calls(calls)

    @staticmethod
    @patch('plinth.actions.superuser_run')
    def test__restore_services(run):
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
        calls = [
            call('service', ['start', 'a-service']),
            call('apache', ['enable', '--name', 'c-service', '--kind', 'site'])
        ]
        run.assert_has_calls(calls)

    @staticmethod
    def test__run_operation():
        """Test that operation runs handler and app hooks."""
        apps = [_get_backup_app('a'), _get_backup_app('b')]
        packet = api.Packet('backup', 'apps', '/', apps)
        packet.apps[0].run_hook = MagicMock()
        packet.apps[1].run_hook = MagicMock()
        handler = MagicMock()
        api._run_operation(handler, packet)
        handler.assert_has_calls([call(packet, encryption_passphrase=None)])

        calls = [call('backup_pre', packet), call('backup_post', packet)]
        packet.apps[0].run_hook.assert_has_calls(calls)
        packet.apps[1].run_hook.assert_has_calls(calls)


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
