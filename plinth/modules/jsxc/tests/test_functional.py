# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for jsxc app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.jsxc]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_install(session_browser):
    """Test installing the app."""
    functional.install(session_browser, 'jsxc')
    assert functional.is_available(session_browser, 'jsxc')


@pytest.mark.backups
def test_backup(session_browser):
    """Test backing up and restoring."""
    functional.backup_create(session_browser, 'jsxc', 'test_jsxc')
    functional.backup_restore(session_browser, 'jsxc', 'test_jsxc')
    assert functional.is_available(session_browser, 'jsxc')
