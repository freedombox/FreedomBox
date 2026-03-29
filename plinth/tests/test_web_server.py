# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for CherryPy web server setup and its components.
"""

import pathlib
from unittest.mock import Mock, call, patch

import pytest

from plinth.web_server import StaticFiles, resolve_static_path


@pytest.fixture(autouse=True)
def fixture_cleanup_static_files():
    """Ensure that global list of static files is clean."""
    StaticFiles._all_instances = {}


def test_static_files_init():
    """Test that static files component is being initialized correctly."""
    component = StaticFiles('test-component')
    assert component.component_id == 'test-component'
    assert component.directory_map is None

    directory_map = {'/a': '/b'}
    component = StaticFiles('test-component', directory_map)
    assert component.directory_map == directory_map


def test_static_files_list():
    """Test that static files components can be listed properly."""
    component1 = StaticFiles('test-component1')
    component2 = StaticFiles('test-component2')

    assert set(StaticFiles.list()) == {component1, component2}


@patch('cherrypy.tree.mount')
def test_static_files_mount(mount, load_cfg):
    """Test that mounting on CherryPy works as expected."""
    directory_map = {'/a': '/b', '/c': '/d'}
    component = StaticFiles('test-component', directory_map)
    component.mount()

    calls = [
        call(
            None, '/freedombox/a', {
                '/': {
                    'tools.staticdir.root': '/b',
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': '.'
                }
            }),
        call(
            None, '/freedombox/c', {
                '/': {
                    'tools.staticdir.root': '/d',
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': '.'
                }
            })
    ]
    mount.assert_has_calls(calls)


@patch('sys.modules')
@patch('plinth.app.App.list')
def test_resolve_static_path(app_list, sys_modules, tmp_path):
    """Test that resolving a static path works as expected."""
    app_list.return_value = []
    expected_path = (pathlib.Path(__file__).parent.parent.parent /
                     'static/theme/icons/test.svg')
    assert resolve_static_path('theme/icons/test.svg') == expected_path

    app = Mock()
    app.app_id = 'test-app'
    app.__module__ = 'test-module'
    app_list.return_value = [app]
    expected_path = (pathlib.Path(__file__).parent.parent.parent /
                     'static/theme/icons/test.svg')

    sys_modules.__getitem__.side_effect = {}.__getitem__
    assert resolve_static_path('theme/icons/test.svg') == expected_path
    with pytest.raises(ValueError, match='Module for app not loaded'):
        resolve_static_path('test-app/test.svg')

    module = Mock()
    sys_modules.__getitem__.side_effect = {'test-module': module}.__getitem__
    with pytest.raises(ValueError,
                       match='Module file for app could not be found'):
        resolve_static_path('test-app/test.svg')

    module.__file__ = tmp_path / 'test-module.py'
    with pytest.raises(ValueError,
                       match='No static directory available for app test-app'):
        resolve_static_path('test-app/test.svg')

    (tmp_path / 'static').mkdir()
    assert resolve_static_path(
        'test-app/test.svg') == tmp_path / 'static/test.svg'
