# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test the component that manages drop-in configuration.
"""

from unittest.mock import Mock, patch

import pytest

from plinth.app import App
from plinth.config import DropinConfigs
from plinth.diagnostic_check import DiagnosticCheck, Result

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = ['plinth.privileged.config']


@pytest.fixture(name='dropin_configs')
def fixture_dropin_configs():
    """Fixture to create a basic drop-in configs component."""

    class AppTest(App):
        app_id = 'test-app'

    app = AppTest()
    component = DropinConfigs('test-component',
                              ['/etc/test/path1', '/etc/path2'])
    app.add(component)

    return component


@pytest.fixture(autouse=True)
def fixture_assert_dropin_config(dropin_configs):
    """Mock asserting dropin config path."""
    with patch('plinth.privileged.config._get_managed_dropin_config') as mock:
        mock.return_value = dropin_configs
        yield


def test_dropin_configs_init(dropin_configs):
    """Test initialization of drop-in configs component."""
    assert dropin_configs.component_id == 'test-component'
    assert dropin_configs.etc_paths[0] == '/etc/test/path1'
    assert dropin_configs.etc_paths[1] == '/etc/path2'
    assert not dropin_configs.copy_only

    component = DropinConfigs('test-component', [], copy_only=False)
    assert not component.copy_only

    component = DropinConfigs('test-component', [], copy_only=True)
    assert component.copy_only


def _assert_symlinks(component, tmp_path, should_exist, copy_only=False):
    """Assert that symlinks exists and they point correctly."""
    for path in component.etc_paths:
        full_path = tmp_path / path.lstrip('/')
        if should_exist:
            target = tmp_path / 'usr/share/freedombox' / path.lstrip('/')
            if copy_only:
                assert full_path.is_file()
                assert full_path.read_text() == target.read_text()
            else:
                assert full_path.is_symlink()
                assert full_path.resolve() == target
        else:
            assert not full_path.exists()


def test_dropin_configs_setup(dropin_configs, tmp_path):
    """Test setup for dropin configs component."""
    with patch('plinth.config.DropinConfigs.ROOT', new=tmp_path):
        is_enabled = Mock()
        App.get('test-app').is_enabled = is_enabled

        is_enabled.return_value = False
        dropin_configs.setup(old_version=0)
        _assert_symlinks(dropin_configs, tmp_path, should_exist=False)

        is_enabled.return_value = True
        dropin_configs.setup(old_version=0)
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True)


def test_dropin_configs_enable_disable_symlinks(dropin_configs, tmp_path):
    """Test enable/disable for dropin configs component for symlinks."""
    with patch('plinth.config.DropinConfigs.ROOT', new=tmp_path):
        # Enable when nothing exists
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True)

        # Disable
        dropin_configs.disable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=False)

        # Enable when a file already exists
        dropin_configs.disable()
        etc_path = dropin_configs.get_etc_path('/etc/test/path1')
        etc_path.touch()
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True)

        # When symlink already exists to wrong location
        dropin_configs.disable()
        etc_path.symlink_to('/blah')
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True)

        # When symlink already exists to correct location
        dropin_configs.disable()
        target_path = dropin_configs.get_target_path('/etc/test/path1')
        etc_path.symlink_to(target_path)
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True)


def test_dropin_configs_enable_disable_copy_only(dropin_configs, tmp_path):
    """Test enable/disable for dropin configs component for copying."""
    with patch('plinth.config.DropinConfigs.ROOT', new=tmp_path):
        dropin_configs.copy_only = True
        for path in ['/etc/test/path1', '/etc/path2']:
            target = dropin_configs.get_target_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('test-config-content')

        # Enable when nothing exists
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True,
                         copy_only=True)

        # Disable
        dropin_configs.disable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=False,
                         copy_only=True)

        # Enable when a file already exists with wrong content
        dropin_configs.disable()
        etc_path = dropin_configs.get_etc_path('/etc/test/path1')
        etc_path.write_text('x-invalid-content')
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True,
                         copy_only=True)

        # When the file is a symlink
        dropin_configs.disable()
        etc_path.symlink_to('/blah')
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True,
                         copy_only=True)

        # When copy already exists with correct content
        dropin_configs.disable()
        etc_path.write_text('test-config-content')
        dropin_configs.enable()
        _assert_symlinks(dropin_configs, tmp_path, should_exist=True,
                         copy_only=True)


def test_dropin_config_diagnose_symlinks(dropin_configs, tmp_path):
    """Test diagnosing dropin configs for symlinks."""
    with patch('plinth.config.DropinConfigs.ROOT', new=tmp_path):
        # Nothing exists
        results = dropin_configs.diagnose()
        assert results == [
            DiagnosticCheck(
                f'dropin-config-{tmp_path}/etc/test/path1',
                'Static configuration {etc_path} is setup properly',
                Result.FAILED, {'etc_path': f'{tmp_path}/etc/test/path1'},
                'test-component'),
            DiagnosticCheck(
                f'dropin-config-{tmp_path}/etc/path2',
                'Static configuration {etc_path} is setup properly',
                Result.FAILED, {'etc_path': f'{tmp_path}/etc/path2'},
                'test-component'),
        ]

        # Proper symlinks exist
        dropin_configs.enable()
        results = dropin_configs.diagnose()
        assert results[0].result == 'passed'
        assert results[1].result == 'passed'

        # A file exists instead of symlink
        dropin_configs.disable()
        etc_path = dropin_configs.get_etc_path('/etc/test/path1')
        etc_path.touch()
        results = dropin_configs.diagnose()
        assert results[0].result == 'failed'

        # Symlink points to wrong location
        dropin_configs.disable()
        etc_path.symlink_to('/blah')
        results = dropin_configs.diagnose()
        assert results[0].result == 'failed'

        # Symlink is recreated
        dropin_configs.enable()
        results = dropin_configs.diagnose()
        assert results[0].result == 'passed'


def test_dropin_config_diagnose_copy_only(dropin_configs, tmp_path):
    """Test diagnosing dropin configs."""
    with patch('plinth.config.DropinConfigs.ROOT', new=tmp_path):
        dropin_configs.copy_only = True
        for path in ['/etc/test/path1', '/etc/path2']:
            target = dropin_configs.get_target_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('test-config-content')

        # Nothing exists
        results = dropin_configs.diagnose()
        assert results[0].result == 'failed'
        assert results[1].result == 'failed'

        # Proper copies exist
        dropin_configs.enable()
        results = dropin_configs.diagnose()
        assert results[0].result == 'passed'
        assert results[1].result == 'passed'

        # A symlink exists instead of a copied file
        dropin_configs.disable()
        etc_path = dropin_configs.get_etc_path('/etc/test/path1')
        etc_path.symlink_to('/blah')
        results = dropin_configs.diagnose()
        assert results[0].result == 'failed'

        # Copied file contains wrong contents
        dropin_configs.disable()
        etc_path.write_text('x-invalid-contents')
        results = dropin_configs.diagnose()
        assert results[0].result == 'failed'
