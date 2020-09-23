# SPDX-License-Identifier: AGPL-3.0-or-later
"""
App component for other apps to use backup/restore functionality.
"""

from plinth import app


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


class BackupRestore(app.FollowerComponent):
    """Component to backup/restore an app."""

    def __init__(self, component_id, config=None, data=None, secrets=None,
                 services=None):
        """Initialize the backup/restore component."""
        super().__init__(component_id)

        _validate_directories_and_files(config)
        self.config = config or {}
        _validate_directories_and_files(data)
        self.data = data or {}
        _validate_directories_and_files(secrets)
        self.secrets = secrets or {}
        _validate_services(services)
        self.services = services or []

        self.has_data = bool(config) or bool(data) or bool(secrets)

    def __eq__(self, other):
        """Check if this component is same as another."""
        return self.component_id == other.component_id

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

        return manifest

    def backup_pre(self, packet):
        """Perform any special operations before backup."""

    def backup_post(self, packet):
        """Perform any special operations after backup."""

    def restore_pre(self, packet):
        """Perform any special operations before restore."""

    def restore_post(self, packet):
        """Perform any special operations after restore."""
