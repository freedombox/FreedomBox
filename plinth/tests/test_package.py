# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for package module.
"""

import unittest
from unittest.mock import Mock, call, patch

import pytest

from plinth.app import App
from plinth.errors import MissingPackageError
from plinth.modules.diagnostics.check import DiagnosticCheck, Result
from plinth.package import Package, Packages, packages_installed


@pytest.fixture(autouse=True)
def fixture_clean_apps():
    """Fixture to ensure clean set of global apps."""
    App._all_apps = {}


class TestPackageExpressions(unittest.TestCase):

    def test_package(self):
        """Test resolving package names."""
        package = Package('python3')
        assert package.possible() == ['python3']
        assert package.actual() == 'python3'

        package = Package('unknown-package')
        assert package.possible() == ['unknown-package']
        self.assertRaises(MissingPackageError, package.actual)

    def test_package_or_expression(self):
        """Test resolving package OR expressions."""
        expression = Package('python3') | Package('unknown-package')
        assert expression.possible() == ['python3', 'unknown-package']
        assert expression.actual() == 'python3'

        expression = Package('unknown-package') | Package('python3')
        assert expression.possible() == ['unknown-package', 'python3']
        assert expression.actual() == 'python3'

        # When both packages are available, prefer the first.
        expression = Package('bash') | Package('dash')
        assert expression.possible() == ['bash', 'dash']
        assert expression.actual() == 'bash'

        expression = Package('unknown-package') | Package(
            'another-unknown-package')
        assert expression.possible() == [
            'unknown-package', 'another-unknown-package'
        ]
        self.assertRaises(MissingPackageError, expression.actual)


def test_packages_init():
    """Test initialization of packages component."""
    component = Packages('test-component', ['foo', 'bar'])
    assert component.possible_packages == ['foo', 'bar']
    assert component.component_id == 'test-component'
    assert not component.skip_recommends
    assert component.conflicts == []
    assert component.conflicts_action is None

    with pytest.raises(ValueError):
        Packages(None, [])

    component = Packages('test-component', [], skip_recommends=True,
                         conflicts=['conflict1', 'conflict2'],
                         conflicts_action=Packages.ConflictsAction.IGNORE)
    assert component.possible_packages == []
    assert component.skip_recommends
    assert component.conflicts == ['conflict1', 'conflict2']
    assert component.conflicts_action == Packages.ConflictsAction.IGNORE


def test_packages_get_actual_packages():
    """Test resolving of package expressions to actual packages."""
    component = Packages('test-component', ['python3'])
    assert component.get_actual_packages() == ['python3']

    component = Packages('test-component',
                         [Package('unknown-package') | Package('python3')])
    assert component.get_actual_packages() == ['python3']

    component = Packages('test-component', [], skip_recommends=True,
                         conflicts=['conflict1', 'conflict2'],
                         conflicts_action=Packages.ConflictsAction.IGNORE)
    assert component.get_actual_packages() == []


@patch('plinth.package.install')
def test_packages_setup(install):
    """Test setting up packages component."""

    class TestApp(App):
        """Test app"""
        app_id = 'test-app'

    component = Packages('test-component', ['python3', 'bash'])
    app = TestApp()
    app.add(component)
    app.setup(old_version=3)
    install.assert_has_calls(
        [call(['python3', 'bash'], skip_recommends=False)])

    component = Packages('test-component', ['bash', 'perl'],
                         skip_recommends=True)
    app = TestApp()
    app.add(component)
    app.setup(old_version=3)
    install.assert_has_calls([call(['bash', 'perl'], skip_recommends=True)])

    component = Packages('test-component',
                         [Package('python3') | Package('unknown-package')])
    app = TestApp()
    app.add(component)
    app.setup(old_version=3)
    install.assert_has_calls([call(['python3'], skip_recommends=False)])


@patch('plinth.package.packages_installed')
@patch('plinth.package.uninstall')
@patch('plinth.package.install')
def test_packages_setup_with_conflicts(install, uninstall, packages_installed):
    """Test setting up packages with conflicts."""
    packages_installed.return_value = ['exim4-base']

    component = Packages('test-component', ['bash'], conflicts=['exim4-base'],
                         conflicts_action=Packages.ConflictsAction.REMOVE)
    component.setup(old_version=0)
    uninstall.assert_has_calls([call(['exim4-base'], purge=False)])
    install.assert_has_calls([call(['bash'], skip_recommends=False)])

    uninstall.reset_mock()
    install.reset_mock()
    component = Packages('test-component', ['bash'], conflicts=['exim4-base'])
    component.setup(old_version=0)
    uninstall.assert_not_called()
    install.assert_has_calls([call(['bash'], skip_recommends=False)])

    uninstall.reset_mock()
    install.reset_mock()
    component = Packages('test-component', ['bash'],
                         conflicts=['exim4-base', 'not-installed-package'],
                         conflicts_action=Packages.ConflictsAction.IGNORE)
    component.setup(old_version=0)
    uninstall.assert_not_called()
    install.assert_has_calls([call(['bash'], skip_recommends=False)])


@patch('plinth.package.uninstall')
def test_packages_uninstall(uninstall):
    """Test uninstalling packages component."""

    class TestApp(App):
        """Test app"""
        app_id = 'test-app'

    component = Packages('test-component', ['python3', 'bash'])
    app = TestApp()
    app.add(component)
    app.uninstall()
    uninstall.assert_has_calls([call(['python3', 'bash'], purge=True)])


@patch('plinth.package.uninstall')
@patch('apt.Cache')
def test_packages_uninstall_exclusion(cache, uninstall):
    """Test excluding packages from other installed apps when uninstalling."""
    cache.return_value = {
        'package11': Mock(candidate=Mock(version='2.0', is_installed=True)),
        'package12': Mock(candidate=Mock(version='3.0', is_installed=False)),
        'package2': Mock(candidate=Mock(version='4.0', is_installed=True)),
        'package3': Mock(candidate=Mock(version='5.0', is_installed=True)),
    }

    class TestApp1(App):
        """Test app."""
        app_id = 'test-app1'

        def __init__(self):
            super().__init__()
            component = Packages('test-component11',
                                 ['package11', 'package2', 'package3'])
            self.add(component)

            component = Packages('test-component12',
                                 ['package12', 'package2', 'package3'])
            self.add(component)

    class TestApp2(App):
        """Test app."""
        app_id = 'test-app2'

        def __init__(self):
            super().__init__()
            component = Packages('test-component2', ['package2'])
            self.add(component)

        def get_setup_state(self):
            return App.SetupState.UP_TO_DATE

    class TestApp3(App):
        """Test app."""
        app_id = 'test-app3'

        def __init__(self):
            super().__init__()
            component = Packages('test-component3', ['package3'])
            self.add(component)

        def get_setup_state(self):
            return App.SetupState.NEEDS_SETUP

    app1 = TestApp1()
    TestApp2()
    TestApp3()
    app1.uninstall()
    uninstall.assert_has_calls([
        call(['package11', 'package3'], purge=True),
        call(['package12', 'package3'], purge=True)
    ])


@patch('apt.Cache')
def test_diagnose(cache):
    """Test checking for latest version of the package."""
    cache.return_value = {
        'package2': Mock(candidate=Mock(version='2.0', is_installed=True)),
        'package3': Mock(candidate=Mock(version='3.0', is_installed=False)),
        'package7': Mock(candidate=Mock(version='4.0', is_installed=True)),
    }
    component = Packages('test-component', [
        'package1', 'package2', 'package3',
        Package('package4') | Package('package5'),
        Package('package6') | Package('package7')
    ])
    results = component.diagnose()
    assert results == [
        DiagnosticCheck(
            'package-available-package1',
            'Package {package_expression} is not available for install',
            Result.FAILED, {'package_expression': 'package1'}),
        DiagnosticCheck(
            'package-latest-package2',
            'Package {package_name} is the latest version ({latest_version})',
            Result.PASSED, {
                'package_name': 'package2',
                'latest_version': '2.0'
            }),
        DiagnosticCheck(
            'package-latest-package3',
            'Package {package_name} is the latest version ({latest_version})',
            Result.WARNING, {
                'package_name': 'package3',
                'latest_version': '3.0'
            }),
        DiagnosticCheck(
            'package-available-package4 | package5',
            'Package {package_expression} is not available for install',
            Result.FAILED, {'package_expression': 'package4 | package5'}),
        DiagnosticCheck(
            'package-latest-package7',
            'Package {package_name} is the latest version ({latest_version})',
            Result.PASSED, {
                'package_name': 'package7',
                'latest_version': '4.0'
            }),
    ]


@patch('plinth.package.packages_installed')
def test_packages_find_conflicts(packages_installed_):
    """Test finding conflicts."""
    packages_installed_.return_value = []
    component = Packages('test-component', ['package3', 'package4'])
    assert component.find_conflicts() is None

    packages_installed_.return_value = []
    component = Packages('test-component', ['package3', 'package4'],
                         conflicts=['package5', 'package6'],
                         conflicts_action=Packages.ConflictsAction.IGNORE)
    assert component.find_conflicts() == []

    packages_installed_.return_value = ['package1', 'package2']
    component = Packages('test-component', ['package3', 'package4'],
                         conflicts=['package1', 'package2'],
                         conflicts_action=Packages.ConflictsAction.IGNORE)
    assert component.find_conflicts() == ['package1', 'package2']


@patch('apt.Cache')
@patch('pathlib.Path')
def test_packages_has_unavailable_packages(path_class, cache):
    """Test checking for unavailable packages."""
    path = Mock()
    path_class.return_value = path
    path.iterdir.return_value = [Mock()]

    component = Packages('test-component', ['package1', 'package2'])
    assert component.has_unavailable_packages() is None

    path.iterdir.return_value = [Mock(), Mock()]
    cache.return_value = ['package1', 'package2']
    assert not component.has_unavailable_packages()

    cache.return_value = ['package1']
    assert component.has_unavailable_packages()


def test_packages_installed():
    """Test packages_installed()."""
    # list as input
    assert len(packages_installed([])) == 0
    assert len(packages_installed(['unknown-package'])) == 0
    assert len(packages_installed(['python3'])) == 1
    # tuples as input
    assert len(packages_installed(())) == 0
    assert len(packages_installed(('unknown-package', ))) == 0
    assert len(packages_installed(('python3', ))) == 1
