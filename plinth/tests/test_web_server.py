# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for CherryPy web server setup and its components.
"""

from unittest.mock import call, patch

import pytest

from plinth.web_server import StaticFiles


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
            None, '/plinth/a', {
                '/': {
                    'tools.staticdir.root': '/b',
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': '.'
                }
            }),
        call(
            None, '/plinth/c', {
                '/': {
                    'tools.staticdir.root': '/d',
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': '.'
                }
            })
    ]
    mount.assert_has_calls(calls)
