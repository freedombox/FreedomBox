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
Test module for App, base class for all applications.
"""

import collections

import pytest

from plinth.app import App, Component, FollowerComponent, LeaderComponent


class LeaderTest(FollowerComponent):
    """Test class for using LeaderComponent in tests."""
    is_leader = True


@pytest.fixture(name='app_with_components')
def fixture_app_with_components():
    """Setup an app with some components."""
    app = App()
    app.add(FollowerComponent('test-follower-1'))
    app.add(FollowerComponent('test-follower-2'))
    app.add(LeaderTest('test-leader-1'))
    app.add(LeaderTest('test-leader-2'))
    return app


def test_app_instantiation():
    """Test that App is instantiated properly."""
    app = App()
    assert isinstance(app.components, collections.OrderedDict)
    assert not app.components


def test_app_add():
    """Test adding a components to an App."""
    app = App()
    component = Component('test-component')
    return_value = app.add(component)
    assert len(app.components) == 1
    assert app.components['test-component'] == component
    assert return_value == app


def test_app_remove(app_with_components):
    """Test removing a component from an App."""
    app = app_with_components
    component = app.components['test-leader-1']
    assert app.remove('test-leader-1') == component
    assert 'test-leader-1' not in app.components


def test_get(app_with_components):
    """Test retrieving a component from an App."""
    app = app_with_components
    component = app.components['test-leader-1']
    assert app.get('test-leader-1') == component
    with pytest.raises(KeyError):
        app.get('x-invalid-component')


def test_app_enable(app_with_components):
    """Test that enabling an app enables components."""
    app_with_components.disable()
    app_with_components.enable()
    for component in app_with_components.components.values():
        assert component.is_enabled()


def test_app_disable(app_with_components):
    """Test that disabling an app disables components."""
    app_with_components.enable()
    app_with_components.disable()
    for component in app_with_components.components.values():
        assert not component.is_enabled()


def test_app_is_enabled(app_with_components):
    """Test checking for app enabled."""
    app = app_with_components
    app.disable()

    # Disabling the components disables that app
    assert not app.is_enabled()

    # Enabling followers will not enable the app
    app.components['test-follower-1'].enable()
    assert not app.is_enabled()
    app.components['test-follower-2'].enable()
    assert not app.is_enabled()

    # Enabling both leaders will enable the app
    app.components['test-leader-1'].enable()
    assert not app.is_enabled()
    app.components['test-leader-2'].enable()
    assert app.is_enabled()

    # Disabling followers has no effect
    app.components['test-follower-1'].disable()
    assert app.is_enabled()


def test_app_set_enabled(app_with_components):
    """Test that setting enabled effects only followers."""
    app = app_with_components

    app.disable()
    app.set_enabled(True)
    assert app.components['test-follower-1'].is_enabled()
    assert not app.components['test-leader-1'].is_enabled()

    app.enable()
    app.set_enabled(False)
    assert not app.components['test-follower-1'].is_enabled()
    assert app.components['test-leader-1'].is_enabled()


def test_component_initialization():
    """Test that component is initialized properly."""
    with pytest.raises(ValueError):
        Component(None)

    component = Component('test-component')
    assert component.component_id == 'test-component'
    assert not component.is_leader


def test_follower_component_initialization():
    """Test that follower component is initialized properly."""
    component = FollowerComponent('test-follower-1')
    assert not component.is_enabled()

    component = FollowerComponent('test-follower-2', False)
    assert not component.is_enabled()

    component = FollowerComponent('test-follower-3', True)
    assert component.is_enabled()


def test_follower_component_enable():
    """Test enabling a follower component."""
    component = FollowerComponent('test-follower-1', False)
    component.enable()
    assert component.is_enabled()


def test_follower_component_disable():
    """Test disabling a follower component."""
    component = FollowerComponent('test-follower-1', True)
    component.disable()
    assert not component.is_enabled()


def test_leader_component_initialization():
    """Test that leader component is initialized properly."""
    component = LeaderComponent('test-leader-1')
    assert component.is_leader


def test_leader_component_is_enabled():
    """Test getting enabled state is not implemented in leader component."""
    component = LeaderComponent('test-leader-1')
    with pytest.raises(NotImplementedError):
        assert component.is_enabled()
