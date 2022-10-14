# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for bind app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.bind]


class TestBindApp(functional.BaseAppTests):
    app_name = 'bind'
    has_service = True
    has_web = False

    def test_set_forwarders(self, session_browser):
        """Test setting forwarders."""
        functional.app_enable(session_browser, 'bind')
        functional.set_forwarders(session_browser, '1.1.1.1')

        functional.set_forwarders(session_browser, '1.1.1.1 1.0.0.1')
        assert functional.get_forwarders(session_browser) == '1.1.1.1 1.0.0.1'

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore."""
        functional.app_enable(session_browser, 'bind')
        functional.set_forwarders(session_browser, '1.1.1.1')
        functional.backup_create(session_browser, 'bind', 'test_bind')

        functional.set_forwarders(session_browser, '1.0.0.1')

        functional.backup_restore(session_browser, 'bind', 'test_bind')
        assert functional.get_forwarders(session_browser) == '1.1.1.1'
