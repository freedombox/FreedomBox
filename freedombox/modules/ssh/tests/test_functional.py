# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ssh app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.system, pytest.mark.ssh]


class TestSshApp(BaseAppTests):
    app_name = 'ssh'
    has_service = True
    has_web = False
    disable_after_tests = False

    # TODO: Improve test_backup_restore to actually check that earlier
    # ssh certificate has been restored.

    def test_enable_disable(self, session_browser):
        """Skip test for enabling and disabling the app."""
        pytest.skip('Avoid restarting SSH server')

    def test_backup_restore(self, session_browser):
        """Skip test for backup and restore operations."""
        pytest.skip('Avoid restarting SSH server')
