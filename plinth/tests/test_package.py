# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for package module.
"""

from unittest.mock import Mock, call, patch

import pytest

from plinth.app import App
from plinth.errors import ActionError
from plinth.package import Packages, packages_installed, remove

setup_helper = Mock()


def test_packages_init():
    """Test initialization of packages component."""
    component = Packages('test-component', ['foo', 'bar'])
    assert component.component_id == 'test-component'
    assert component.packages == ['foo', 'bar']
    assert not component.skip_recommends
    assert component.conflicts is None
    assert component.conflicts_action is None

    with pytest.raises(ValueError):
        Packages(None, [])

    component = Packages('test-component', [], skip_recommends=True,
                         conflicts=['conflict1', 'conflict2'],
                         conflicts_action=Packages.ConflictsAction.IGNORE)
    assert component.packages == []
    assert component.skip_recommends
    assert component.conflicts == ['conflict1', 'conflict2']
    assert component.conflicts_action == Packages.ConflictsAction.IGNORE


def test_packages_setup():
    """Test setting up packages component."""

    class TestApp(App):
        """Test app"""
        app_id = 'test-app'

    component = Packages('test-component', ['foo1', 'bar1'])
    app = TestApp()
    app.add(component)
    setup_helper.reset_mock()
    app.setup(old_version=3)
    setup_helper.install.assert_has_calls(
        [call(['foo1', 'bar1'], skip_recommends=False)])

    component = Packages('test-component', ['foo2', 'bar2'],
                         skip_recommends=True)
    app = TestApp()
    app.add(component)
    setup_helper.reset_mock()
    app.setup(old_version=3)
    setup_helper.install.assert_has_calls(
        [call(['foo2', 'bar2'], skip_recommends=True)])


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
