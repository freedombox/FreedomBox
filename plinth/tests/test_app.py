# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for App, base class for all applications.
"""

import collections
from unittest.mock import Mock, call, patch

import pytest

from plinth.app import App, Component, FollowerComponent, Info, LeaderComponent

# pylint: disable=protected-access


class AppTest(App):
    """Sample App for testing."""
    app_id = 'test-app'


class LeaderTest(FollowerComponent):
    """Test class for using LeaderComponent in tests."""
    is_leader = True

    def diagnose(self):
        """Return diagnostic results."""
        return [('test-result-' + self.component_id, 'success')]


@pytest.fixture(name='app_with_components')
def fixture_app_with_components():
    """Setup an app with some components."""
    app = AppTest()
    app.add(FollowerComponent('test-follower-1'))
    app.add(FollowerComponent('test-follower-2'))
    app.add(LeaderTest('test-leader-1'))
    app.add(LeaderTest('test-leader-2'))
    return app


@pytest.fixture(name='empty_apps', autouse=True)
def fixture_empty_apps():
    """Remove all apps from global list before starting a test."""
    App._all_apps = collections.OrderedDict()


def test_app_instantiation():
    """Test that App is instantiated properly."""
    app = AppTest()
    assert isinstance(app.components, collections.OrderedDict)
    assert not app.components
    assert app.app_id == 'test-app'
    assert app._all_apps['test-app'] == app
    assert len(app._all_apps) == 1


def test_app_get():
    """Test that an app can be correctly retrieved."""
    app = AppTest()
    assert App.get(app.app_id) == app


def test_app_list():
    """Test listing all apps."""
    app = AppTest()
    assert list(App.list()) == [app]


def test_app_add():
    """Test adding a components to an App."""
    app = AppTest()
    component = Component('test-component')
    return_value = app.add(component)
    assert len(app.components) == 1
    assert app.components['test-component'] == component
    assert component.app_id == app.app_id
    assert return_value == app


def test_app_remove(app_with_components):
    """Test removing a component from an App."""
    app = app_with_components
    component = app.components['test-leader-1']
    assert app.remove('test-leader-1') == component
    assert component.app_id is None
    assert 'test-leader-1' not in app.components


def test_get_component(app_with_components):
    """Test retrieving a component from an App."""
    app = app_with_components
    component = app.components['test-leader-1']
    assert app.get_component('test-leader-1') == component
    with pytest.raises(KeyError):
        app.get_component('x-invalid-component')


def test_get_components_of_type(app_with_components):
    """Test retrieving list of components of a given type."""
    app = app_with_components
    components = app.get_components_of_type(FollowerComponent)
    follower_components = [
        app.components['test-follower-1'],
        app.components['test-follower-2'],
        app.components['test-leader-1'],
        app.components['test-leader-2'],
    ]
    assert list(components) == follower_components
    components = app.get_components_of_type(LeaderTest)
    leader_components = [
        app.components['test-leader-1'],
        app.components['test-leader-2'],
    ]
    assert list(components) == leader_components


def test_app_setup(app_with_components):
    """Test that running setup on an app run setup on components."""
    for component in app_with_components.components.values():
        component.setup = Mock()

    app_with_components.setup(old_version=2)
    for component in app_with_components.components.values():
        component.setup.assert_has_calls([call(old_version=2)])


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


def test_app_is_enabled_with_no_leader_components():
    """When there are not leader components, app.is_enabled() returns True."""
    app = AppTest()
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


def test_app_diagnose(app_with_components):
    """Test running diagnostics on an app."""
    results = app_with_components.diagnose()
    assert results == [('test-result-test-leader-1', 'success'),
                       ('test-result-test-leader-2', 'success')]


def test_app_has_diagnostics(app_with_components):
    """Test checking if app has diagnostics implemented."""
    app = app_with_components

    # App with components that has diagnostics
    assert app.has_diagnostics()

    # App with components that don't have diagnostics
    app.remove('test-leader-1')
    app.remove('test-leader-2')
    assert not app.has_diagnostics()

    # App with app-level diagnostics
    with patch.object(AppTest, 'diagnose', return_value=[('test1', 'passed')]):
        assert app.has_diagnostics()


def test_component_initialization():
    """Test that component is initialized properly."""
    with pytest.raises(ValueError):
        Component(None)

    component = Component('test-component')
    assert component.component_id == 'test-component'
    assert not component.is_leader


def test_component_app_property():
    """Test component's app property."""
    component = Component('test-component')
    assert component.app_id is None
    with pytest.raises(KeyError):
        assert not component.app

    app = AppTest()
    app.add(component)
    assert component.app == app


def test_component_setup():
    """Test running setup on component."""
    component = Component('test-component')
    assert component.setup(old_version=1) is None


def test_component_enable():
    """Test running enable on component."""
    component = Component('test-component')
    assert component.enable() is None


def test_component_disable():
    """Test running disable on component."""
    component = Component('test-component')
    assert component.disable() is None


def test_component_diagnose():
    """Test running diagnostics on component."""
    component = Component('test-component')
    assert component.diagnose() == []


def test_component_has_diagnostics():
    """Test checking if component has diagnostics implemented."""
    component = LeaderTest('test-leader-1')
    assert component.has_diagnostics()

    component = FollowerComponent('test-follower-1')
    assert not component.has_diagnostics()


def test_follower_component_initialization():
    """Test that follower component is initialized properly."""
    component = FollowerComponent('test-follower-1')
    assert not component.is_enabled()

    component = FollowerComponent('test-follower-2', False)
    assert not component.is_enabled()

    component = FollowerComponent('test-follower-3', True)
    assert component.is_enabled()


def test_follower_component_set_enabled():
    """Test setting internal enabled state a follower component."""
    component = FollowerComponent('test-follower-1', False)
    component.set_enabled(True)
    assert component.is_enabled()
    component.set_enabled(False)
    assert not component.is_enabled()


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


def test_info_initialization_without_args():
    """Test initializing the Info component without arguments."""
    info = Info('test-app', 3)
    assert info.component_id == 'test-app-info'
    assert info.app_id == 'test-app'
    assert info.version == 3
    assert not info.is_essential
    assert info.depends == []
    assert info.name is None
    assert info.icon is None
    assert info.icon_filename is None
    assert info.short_description is None
    assert info.description is None
    assert info.manual_page is None
    assert info.clients is None


def test_info_initialization_with_args():
    """Test initializing the Info component with arguments."""
    clients = [{
        'name': 'test',
        'platforms': [{
            'type': 'web',
            'url': 'test-url'
        }]
    }]
    info = Info('test-app', 3, is_essential=True, depends=['test-app-2'],
                name='Test App', icon='fa-test', icon_filename='test-icon',
                short_description='For Test', description='Test description',
                manual_page='Test', clients=clients)
    assert info.is_essential
    assert info.depends == ['test-app-2']
    assert info.name == 'Test App'
    assert info.icon == 'fa-test'
    assert info.icon_filename == 'test-icon'
    assert info.short_description == 'For Test'
    assert info.description == 'Test description'
    assert info.manual_page == 'Test'
    assert info.clients == clients


def test_info_clients_validation():
    """Test clients parameter validation during initialization."""
    with pytest.raises(AssertionError):
        Info('test-app', 3, clients='invalid')

    clients = [{
        'name': 'test',
        'platforms': [{
            'type': 'web',
            'url': 'test-url'
        }]
    }]
    Info('test-app', 3, clients=clients)
