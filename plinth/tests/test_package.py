# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for package module.
"""

from unittest.mock import call, patch

from plinth.errors import ActionError
from plinth.package import packages_installed, remove


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
