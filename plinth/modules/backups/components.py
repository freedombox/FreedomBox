# SPDX-License-Identifier: AGPL-3.0-or-later
"""
App component for other apps to use backup/restore functionality.
"""

import copy
import json

from plinth import actions, app


def _validate_directories_and_files(section):
    """Validate directories and files keys in a section."""
    if not section:
        return

    assert isinstance(section, dict)

    if 'directories' in section:
        assert isinstance(section['directories'], list)
        for directory in section['directories']:
            assert isinstance(directory, str)

    if 'files' in section:
        assert isinstance(section['files'], list)
        for file_path in section['files']:
            assert isinstance(file_path, str)


def _validate_services(services):
    """Validate services manifest provided as list."""
    if not services:
        return

    assert isinstance(services, list)
    for service in services:
        assert isinstance(service, (str, dict))
        if isinstance(service, dict):
            _validate_service(service)


def _validate_service(service):
    """Validate a service manifest provided as a dictionary."""
    assert isinstance(service['name'], str)
    assert isinstance(service['type'], str)
    assert service['type'] in ('apache', 'uwsgi', 'system')
    if service['type'] == 'apache':
        assert service['kind'] in ('config', 'site', 'module')


def _validate_settings(settings):
    """Validate settings stored by an in kvstore."""
    if not settings:
        return

    assert isinstance(settings, list)
    for setting in settings:
        assert isinstance(setting, str)


class BackupRestore(app.FollowerComponent):
    """Component to backup/restore an app."""

    def __init__(self, component_id, config=None, data=None, secrets=None,
                 services=None, settings=None):
        """Initialize the backup/restore component."""
        super().__init__(component_id)

        _validate_directories_and_files(config)
        self.config = config or {}
        _validate_directories_and_files(data)
        self._data = data or {}
        _validate_directories_and_files(secrets)
        self.secrets = secrets or {}
        _validate_services(services)
        self.services = services or []
        _validate_settings(settings)
        self.settings = settings or []

        self.has_data = (bool(config) or bool(data) or bool(secrets)
                         or bool(settings))

    def __eq__(self, other):
        """Check if this component is same as another."""
        return self.component_id == other.component_id

    @property
    def data(self):
        """Add additional files to data files list."""
        data = copy.deepcopy(self._data)
        settings_file = self._get_settings_file()
        if settings_file:
            data.setdefault('files', []).append(settings_file)

        return data

    @property
    def manifest(self):
        """Return the backup details as a dictionary."""
        manifest = {}
        if self.config:
            manifest['config'] = self.config

        if self.secrets:
            manifest['secrets'] = self.secrets

        if self.data:
            manifest['data'] = self.data

        if self.services:
            manifest['services'] = self.services

        if self.settings:
            manifest['settings'] = self.settings

        return manifest

    def backup_pre(self, packet):
        """Perform any special operations before backup."""
        self._settings_backup_pre()

    def backup_post(self, packet):
        """Perform any special operations after backup."""

    def restore_pre(self, packet):
        """Perform any special operations before restore."""

    def restore_post(self, packet):
        """Perform any special operations after restore."""
        self._settings_restore_post()

    def _get_settings_file(self):
        """Return the settings file path to list of files to backup."""
        if not self.settings or not self.app_id:
            return None

        data_path = '/var/lib/plinth/backups-data/'
        return data_path + f'{self.app_id}-settings.json'

    def _settings_backup_pre(self):
        """Read keys from kvstore and store them in a file to backup."""
        if not self.settings:
            return

        from plinth import kvstore
        data = {}
        for key in self.settings:
            try:
                data[key] = kvstore.get(key)
            except Exception:
                pass

        input_ = json.dumps(data).encode()
        actions.superuser_run('backups',
                              ['dump-settings', '--app-id', self.app_id],
                              input=input_)

    def _settings_restore_post(self):
        """Read from a file and restore keys to kvstore."""
        if not self.settings:
            return

        output = actions.superuser_run(
            'backups', ['load-settings', '--app-id', self.app_id])
        data = json.loads(output)

        from plinth import kvstore
        for key, value in data.items():
            kvstore.set(key, value)
