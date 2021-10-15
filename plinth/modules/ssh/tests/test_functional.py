# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ssh app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.ssh]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'ssh')
    yield
    functional.app_enable(session_browser, 'ssh')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'ssh')

    functional.app_enable(session_browser, 'ssh')
    assert functional.service_is_running(session_browser, 'ssh')

    functional.app_disable(session_browser, 'ssh')
    assert functional.service_is_not_running(session_browser, 'ssh')


# TODO: Improve this to actually check that earlier ssh certificate has been
# restored.
@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore."""
    functional.app_enable(session_browser, 'ssh')
    functional.backup_create(session_browser, 'ssh', 'test_ssh')
    functional.backup_restore(session_browser, 'ssh', 'test_ssh')
    assert functional.service_is_running(session_browser, 'ssh')
