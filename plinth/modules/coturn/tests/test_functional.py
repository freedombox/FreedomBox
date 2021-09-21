# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for coturn app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.coturn]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'coturn')
    yield
    functional.app_disable(session_browser, 'coturn')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'coturn')

    functional.app_enable(session_browser, 'coturn')
    assert functional.service_is_running(session_browser, 'coturn')

    functional.app_disable(session_browser, 'coturn')
    assert functional.service_is_not_running(session_browser, 'coturn')


@pytest.mark.backups
def test_backup(session_browser):
    # TODO: Improve this by checking that secret and domain did not change
    functional.app_enable(session_browser, 'coturn')
    functional.backup_create(session_browser, 'coturn', 'test_coturn')
    functional.backup_restore(session_browser, 'coturn', 'test_coturn')
    assert functional.service_is_running(session_browser, 'coturn')
