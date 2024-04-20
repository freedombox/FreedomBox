# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for App, base class for all applications.
"""

import collections
from unittest.mock import Mock, call, patch

import pytest

from plinth.app import (App, Component, EnableState, FollowerComponent, Info,
                        LeaderComponent, apps_init)
from plinth.diagnostic_check import DiagnosticCheck, Result

# pylint: disable=protected-access


class AppTest(App):
    """Sample App for testing."""
    app_id = 'test-app'


class AppSetupTest(App):
    """Sample App for testing setup operations."""
    app_id = 'test-app-setup'

    def __init__(self):
        super().__init__()
        info = Info('test-app-setup', 3)
        self.add(info)


class LeaderTest(FollowerComponent):
    """Test class for using LeaderComponent in tests."""
    is_leader = True

    def diagnose(self) -> list[DiagnosticCheck]:
        """Return diagnostic results."""
        return [
            DiagnosticCheck('test-result-' + self.component_id,
                            'test-result-' + self.component_id, Result.PASSED)
        ]


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
    assert app.can_be_disabled
    assert not app.locked
    assert app.configure_when_disabled


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
    """Test that running setup on an app runs setup on components."""
    for component in app_with_components.components.values():
        component.setup = Mock()

    app_with_components.setup(old_version=2)
    for component in app_with_components.components.values():
        component.setup.assert_has_calls([call(old_version=2)])


def test_app_uninstall(app_with_components):
    """Test that running uninstall on an app runs uninstall on components."""
    for component in app_with_components.components.values():
        component.uninstall = Mock()

    app_with_components.uninstall()
    for component in app_with_components.components.values():
        component.uninstall.assert_has_calls([call()])


@pytest.mark.django_db
def test_setup_state():
    """Test retrieving the current setup state of the app."""
    app = AppSetupTest()
    app.info.version = 3

    app.set_setup_version(3)
    assert app.get_setup_state() == App.SetupState.UP_TO_DATE
    assert not app.needs_setup()

    app.set_setup_version(0)
    assert app.get_setup_state() == App.SetupState.NEEDS_SETUP
    assert app.needs_setup()

    app.set_setup_version(2)
    assert app.get_setup_state() == App.SetupState.NEEDS_UPDATE
    assert not app.needs_setup()


@pytest.mark.django_db
def test_get_set_setup_version():
    """Setting and getting the setup version of the app."""
    app = AppSetupTest()

    from plinth import models
    try:
        models.Module.objects.get(pk=app.app_id).delete()
    except models.Module.DoesNotExist:
        pass
    assert app.get_setup_version() == 0

    app.set_setup_version(5)
    assert app.get_setup_version() == 5


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
    assert results == [
        DiagnosticCheck('test-result-test-leader-1',
                        'test-result-test-leader-1', Result.PASSED),
        DiagnosticCheck('test-result-test-leader-2',
                        'test-result-test-leader-2', Result.PASSED),
    ]


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
    with patch.object(
            AppTest, 'diagnose',
            return_value=[DiagnosticCheck('test1', 'test1', Result.PASSED)]):
        assert app.has_diagnostics()


@patch('plinth.setup.run_setup_on_app')
def test_app_repair(_run_setup_on_app, app_with_components):
    """Test running repair on an app."""
    component = app_with_components.get_component('test-follower-1')
    component.repair = Mock(return_value=True)

    check1 = DiagnosticCheck('check1', 'check1', Result.FAILED, {})
    check2 = DiagnosticCheck('check2', 'check2', Result.WARNING, {})
    check3 = DiagnosticCheck('check3', 'check3', Result.FAILED, {},
                             'test-follower-1')
    should_rerun_setup = app_with_components.repair([])
    assert not should_rerun_setup

    should_rerun_setup = app_with_components.repair([check1])
    assert should_rerun_setup

    should_rerun_setup = app_with_components.repair([check2])
    assert should_rerun_setup

    should_rerun_setup = app_with_components.repair([check1, check2])
    assert should_rerun_setup
    component.repair.assert_not_called()

    should_rerun_setup = app_with_components.repair([check3])
    assert should_rerun_setup
    assert component.repair.mock_calls == [call([check3])]

    component.repair = Mock(return_value=False)
    should_rerun_setup = app_with_components.repair([check3])
    assert not should_rerun_setup


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


def test_component_uninstall():
    """Test running uninstall on component."""
    component = Component('test-component')
    assert component.uninstall() is None


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


@patch('plinth.setup.run_setup_on_app')
def test_component_repair(_run_setup_on_app):
    """Test running repair on component."""
    component = Component('test-component')
    assert component.repair(['test-check'])


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


def test_enable_state_key(app_with_components):
    """Test getting the storage key for enable state component."""
    component = EnableState('enable-state-1')
    with pytest.raises(KeyError):
        assert component.key

    app_with_components.add(component)
    assert component.key == app_with_components.app_id + '_enable'


@pytest.mark.django_db
def test_enable_state_enable_disable(app_with_components):
    """Test enabling/disabling enable state component."""
    component = EnableState('enable-state-1')
    app_with_components.add(component)
    assert not component.is_enabled()
    component.enable()
    assert component.is_enabled()
    component.disable()
    assert not component.is_enabled()


class ModuleTest1:
    """A test module with an app."""

    class App1(App):
        """A non-essential app that depends on another."""
        app_id = 'app1'

        def __init__(self):
            super().__init__()
            self.add(Info('app1', version=1, depends=['app3']))


class ModuleTest2:
    """A test module with multiple apps."""

    class App2(App):
        """An essential app."""
        app_id = 'app2'

        def __init__(self):
            super().__init__()
            self.add(Info('app2', version=1, is_essential=True))

    class App3(App):
        """An non-essential app that is depended on by another."""
        app_id = 'app3'

        def __init__(self):
            super().__init__()
            self.add(Info('app3', version=1))


@patch('plinth.module_loader.loaded_modules')
def test_apps_init(loaded_modules):
    """Test that initializing all apps works."""
    loaded_modules.items.return_value = [('test1', ModuleTest1()),
                                         ('test2', ModuleTest2())]

    apps_init()
    assert list(App._all_apps.keys()) == ['app2', 'app3', 'app1']


class ModuleCircularTest:
    """A test module with apps depending on each other."""

    class App1(App):
        """An app depending on app2."""
        app_id = 'app1'

        def __init__(self):
            super().__init__()
            self.add(Info('app1', version=1, depends=['app2']))

    class App2(App):
        """An app depending on app1."""
        app_id = 'app2'

        def __init__(self):
            super().__init__()
            self.add(Info('app2', version=1, depends=['app1']))

    class App3(App):
        """An app without dependencies."""
        app_id = 'app3'

        def __init__(self):
            super().__init__()
            self.add(Info('app3', version=1))


@patch('plinth.module_loader.loaded_modules')
def test_apps_init_circular_depends(loaded_modules):
    """Test initializing apps with circular dependencies."""
    loaded_modules.items.return_value = [('test', ModuleCircularTest())]

    apps_init()
    assert list(App._all_apps.keys()) == ['app3']
