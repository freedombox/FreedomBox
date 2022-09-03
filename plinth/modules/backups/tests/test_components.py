# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test the App components provides by backups app.
"""

from unittest.mock import call, patch

import pytest

from plinth import kvstore

from .. import components
from ..components import BackupRestore

# pylint: disable=protected-access


@pytest.fixture(name='backup_restore')
def fixture_backup_restore():
    """Fixture to create a domain type after clearing all existing ones."""
    value = {'files': ['a', 'b'], 'directories': ['a', 'b']}
    services = ['service-1', {'type': 'system', 'name': 'service-2'}]
    settings = ['setting-1', 'setting-2']
    return BackupRestore('test-backup-restore', config=value, data=value,
                         secrets=value, services=services, settings=settings)


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
    assert component.settings == []
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


def test_backup_restore_init_settings():
    """Test initialization of the backup restore object."""
    with pytest.raises(AssertionError):
        BackupRestore('test-backup-restore', settings='invalid-value')

    settings = ['setting1', 'setting2']
    component = BackupRestore('test-backup-restore', settings=settings)
    assert component.settings == settings
    assert component.has_data
    assert component.data == {}

    component.app_id = 'testapp'
    settings_file = '/var/lib/plinth/backups-data/testapp-settings.json'
    assert component.data == {'files': [settings_file]}


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
    assert manifest['settings'] == backup_restore.settings

    assert BackupRestore('test-backup-restore').manifest == {}


def test_backup_restore_hooks(backup_restore):
    """Test running hooks on backup restore object."""
    packet = None
    backup_restore.backup_post(packet)
    backup_restore.restore_pre(packet)


@pytest.mark.django_db
@patch('plinth.modules.backups.privileged.dump_settings')
def test_backup_restore_backup_pre(dump_settings, backup_restore):
    """Test running backup-pre hook."""
    packet = None
    kvstore.set('setting-1', 'value-1')
    backup_restore.app_id = 'testapp'

    component = BackupRestore('test-backup-restore')
    component.backup_pre(packet)
    dump_settings.assert_has_calls([])

    backup_restore.backup_pre(packet)
    dump_settings.assert_has_calls([call('testapp', {'setting-1': 'value-1'})])


@pytest.mark.django_db
@patch('plinth.modules.backups.privileged.load_settings')
def test_backup_restore_restore_post(load_settings, backup_restore):
    """Test running restore-post hook."""
    packet = None
    backup_restore.app_id = 'testapp'

    component = BackupRestore('test-backup-restore')
    component.restore_post(packet)
    load_settings.assert_has_calls([])

    output = {'setting-1': 'value-1'}
    load_settings.return_value = output
    backup_restore.restore_post(packet)
    load_settings.assert_has_calls([call('testapp')])

    assert kvstore.get('setting-1') == 'value-1'
    with pytest.raises(Exception):
        kvstore.get('setting-2')
