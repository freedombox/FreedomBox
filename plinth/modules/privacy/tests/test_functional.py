# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for privacy app."""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.privacy]


class TestPrivacyApp(functional.BaseAppTests):
    """Tests for privacy app."""

    app_name = 'privacy'
    has_service = False
    has_web = False
    disable_after_tests = False

    @pytest.fixture(autouse=True)
    def fixture_background(self, session_browser):
        """Login, install, and enable the app."""
        functional.login(session_browser)
        functional.nav_to_module(session_browser, self.app_name)
        yield

    def test_enable_disable(self, session_browser):
        """Skip test for enabling and disabling the app."""
        pytest.skip('Can not be disabled')

    @pytest.mark.backups
    def test_enable_disable_popcon(self, session_browser):
        """Test that popcon can be enable/disabled."""
        functional.change_checkbox_status(session_browser, self.app_name,
                                          'id_enable_popcon', 'disabled')
        functional.change_checkbox_status(session_browser, self.app_name,
                                          'id_enable_popcon', 'enabled')
        assert session_browser.find_by_id('id_enable_popcon').checked
        functional.change_checkbox_status(session_browser, self.app_name,
                                          'id_enable_popcon', 'disabled')
        assert not session_browser.find_by_id('id_enable_popcon').checked

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test that backup and restore operations work on the app."""
        functional.change_checkbox_status(session_browser, self.app_name,
                                          'id_enable_popcon', 'disabled')
        functional.backup_create(session_browser, self.app_name,
                                 'test_' + self.app_name)
        functional.nav_to_module(session_browser, self.app_name)
        functional.change_checkbox_status(session_browser, self.app_name,
                                          'id_enable_popcon', 'enabled')
        functional.backup_restore(session_browser, self.app_name,
                                  'test_' + self.app_name)
        functional.nav_to_module(session_browser, self.app_name)
        assert not session_browser.find_by_id('id_enable_popcon').checked

    def test_uninstall(self, session_browser):
        """Skip test for uninstall."""
        pytest.skip('Essential app')
