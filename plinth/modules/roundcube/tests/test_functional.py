# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for roundcube app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.roundcube]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'roundcube')
    yield
    functional.app_disable(session_browser, 'roundcube')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'roundcube')

    functional.app_enable(session_browser, 'roundcube')
    assert functional.is_available(session_browser, 'roundcube')

    functional.app_disable(session_browser, 'roundcube')
    assert not functional.is_available(session_browser, 'roundcube')


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore."""
    functional.app_enable(session_browser, 'roundcube')
    functional.backup_create(session_browser, 'roundcube', 'test_roundcube')
    functional.backup_restore(session_browser, 'roundcube', 'test_roundcube')
    assert functional.is_available(session_browser, 'roundcube')
