# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for security app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.security]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of configuration."""
    functional.backup_create(session_browser, 'security', 'test_security')
