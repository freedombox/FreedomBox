# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for package module.
"""

import unittest
from unittest.mock import Mock, call, patch

import pytest

from plinth.app import App
from plinth.errors import ActionError, MissingPackageError
from plinth.package import Package, Packages, packages_installed, remove

setup_helper = Mock()


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
    assert component.conflicts is None
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


def test_packages_setup():
    """Test setting up packages component."""

    class TestApp(App):
        """Test app"""
        app_id = 'test-app'

    component = Packages('test-component', ['python3', 'bash'])
    app = TestApp()
    app.add(component)
    setup_helper.reset_mock()
    app.setup(old_version=3)
    setup_helper.install.assert_has_calls(
        [call(['python3', 'bash'], skip_recommends=False)])

    component = Packages('test-component', ['bash', 'perl'],
                         skip_recommends=True)
    app = TestApp()
    app.add(component)
    setup_helper.reset_mock()
    app.setup(old_version=3)
    setup_helper.install.assert_has_calls(
        [call(['bash', 'perl'], skip_recommends=True)])

    component = Packages('test-component',
                         [Package('python3') | Package('unknown-package')])
    app = TestApp()
    app.add(component)
    setup_helper.reset_mock()
    app.setup(old_version=3)
    setup_helper.install.assert_has_calls(
        [call(['python3'], skip_recommends=False)])


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
    assert 'not available for install' in results[0][0]
    assert results[0][1] == 'failed'
    assert '(2.0)' in results[1][0]
    assert results[1][1] == 'passed'
    assert '(3.0)' in results[2][0]
    assert results[2][1] == 'warning'
    assert 'not available for install' in results[3][0]
    assert results[3][1] == 'failed'
    assert '(4.0)' in results[4][0]
    assert results[4][1] == 'passed'


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


@patch('plinth.actions.superuser_run')
def test_remove(run):
    """Test removing packages."""
    remove(['package1', 'package2'])
    run.assert_has_calls(
        [call('packages', ['remove', '--packages', 'package1', 'package2'])])

    run.reset_mock()
    run.side_effect = ActionError()
    remove(['package1'])
    run.assert_has_calls(
        [call('packages', ['remove', '--packages', 'package1'])])
