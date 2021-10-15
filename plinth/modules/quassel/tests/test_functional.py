# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for quassel app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.quassel]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'quassel')
    yield
    functional.app_disable(session_browser, 'quassel')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'quassel')

    functional.app_enable(session_browser, 'quassel')
    assert functional.service_is_running(session_browser, 'quassel')

    functional.app_disable(session_browser, 'quassel')
    assert functional.service_is_not_running(session_browser, 'quassel')


# TODO: Improve this to actually check that data configured servers is
# restored.
@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of app data."""
    functional.app_enable(session_browser, 'quassel')
    functional.backup_create(session_browser, 'quassel', 'test_quassel')
    functional.backup_restore(session_browser, 'quassel', 'test_quassel')
    assert functional.service_is_running(session_browser, 'quassel')
