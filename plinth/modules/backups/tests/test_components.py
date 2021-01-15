# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test the App components provides by backups app.
"""

import pytest

from .. import components
from ..components import BackupRestore

# pylint: disable=protected-access


@pytest.fixture(name='backup_restore')
def fixture_backup_restore():
    """Fixture to create a domain type after clearing all existing ones."""
    value = {'files': ['a', 'b'], 'directories': ['a', 'b']}
    services = ['service-1', {'type': 'system', 'name': 'service-2'}]
    return BackupRestore('test-backup-restore', config=value, data=value,
                         secrets=value, services=services)


@pytest.mark.parametrize('section', [
    None,
    {
        'directories': ['a', 'b']
    },
    {
        'files': ['a', 'b']
    },
    {
        'directories': ['a'],
        'files': ['a']
    },
    {
        'extra': 'value'
    },
])
def test_valid_directories_and_files(section):
    """Test that valid values of files and directories."""
    components._validate_directories_and_files(section)


@pytest.mark.parametrize('section', [
    'invalid',
    10,
    ['invalid'],
    {
        'files': None
    },
    {
        'files': 10
    },
    {
        'files': {}
    },
    {
        'files': [10],
    },
    {
        'files': [None],
    },
    {
        'files': [[]],
    },
    {
        'directories': None
    },
    {
        'directories': [10],
    },
])
def test_invalid_directories_and_files(section):
    """Test that invalid values of files and directories."""
    with pytest.raises(AssertionError):
        components._validate_directories_and_files(section)


@pytest.mark.parametrize('services', [
    None,
    [],
    ['service'],
    [{
        'type': 'uwsgi',
        'name': 'service'
    }],
    [{
        'type': 'system',
        'name': 'service'
    }],
    [{
        'type': 'apache',
        'name': 'service',
        'kind': 'config'
    }],
    [{
        'type': 'apache',
        'name': 'service',
        'kind': 'site'
    }],
    [{
        'type': 'apache',
        'name': 'service',
        'kind': 'module'
    }],
])
def test_valid_services(services):
    """Test that valid values of services."""
    components._validate_services(services)


@pytest.mark.parametrize('services', [
    10,
    'invalid',
    [10],
    [[]],
    [{}],
    [{
        'type': 'invalid',
        'name': 'service'
    }],
    [{
        'type': 10,
        'name': 'service'
    }],
    [{
        'type': 'system',
        'name': 10
    }],
    [{
        'type': 'system',
        'name': None
    }],
    [{
        'type': 'system',
        'name': []
    }],
    [{
        'type': 'apache',
        'name': 'service'
    }],
    [{
        'type': 'apache',
        'name': 'service',
        'kind': 'invalid-kind'
    }],
])
def test_invalid_services(services):
    """Test that invalid values of services."""
    with pytest.raises((AssertionError, KeyError)):
        components._validate_services(services)


def test_backup_restore_init_default_arguments():
    """Test initialization of the backup restore object."""
    component = BackupRestore('test-backup-restore')
    assert component.component_id == 'test-backup-restore'
    assert component.config == {}
    assert component.data == {}
    assert component.secrets == {}
    assert component.services == []
    assert not component.has_data


@pytest.mark.parametrize('key', ['config', 'data', 'secrets'])
def test_backup_restore_init(key):
    """Test initialization of the backup restore object."""
    with pytest.raises(AssertionError):
        BackupRestore('test-backup-restore', **{key: 'invalid-value'})

    value = {'files': ['a', 'b'], 'directories': ['a', 'b']}
    component = BackupRestore('test-backup-restore', **{key: value})
    assert getattr(component, key) == value
    assert component.has_data


def test_backup_restore_init_services():
    """Test initialization of the backup restore object."""
    with pytest.raises(AssertionError):
        BackupRestore('test-backup-restore', services='invalid-value')

    services = ['service-1', {'type': 'system', 'name': 'service-2'}]
    component = BackupRestore('test-backup-restore', services=services)
    assert component.services == services
    assert not component.has_data


def test_backup_restore_equal(backup_restore):
    """Test equality operator on the backup restore object."""
    assert backup_restore == BackupRestore('test-backup-restore')
    assert backup_restore != BackupRestore('test-different')


def test_backup_restore_manifest(backup_restore):
    """Test manifest retrieval from backup restore object."""
    manifest = backup_restore.manifest
    assert isinstance(manifest, dict)
    assert manifest['config'] == backup_restore.config
    assert manifest['data'] == backup_restore.data
    assert manifest['secrets'] == backup_restore.secrets
    assert manifest['services'] == backup_restore.services

    assert BackupRestore('test-backup-restore').manifest == {}


def test_backup_restore_hooks(backup_restore):
    """Test running hooks on backup restore object."""
    packet = None
    backup_restore.backup_pre(packet)
    backup_restore.backup_post(packet)
    backup_restore.restore_pre(packet)
    backup_restore.restore_post(packet)
