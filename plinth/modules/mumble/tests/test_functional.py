# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mumble app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.mumble]


class TestMumbleApp(functional.BaseAppTests):
    app_name = 'mumble'
    has_service = True
    has_web = False

    # TODO: Requires a valid domain with certificates to complete setup.
    check_diagnostics = False

    @staticmethod
    def test_change_root_channel_name(session_browser):
        """Test changing root channel name."""
        functional.set_app_form_value(session_browser, 'mumble',
                                      'id_root_channel_name', 'test-channel')
        assert session_browser.find_by_id(
            'id_root_channel_name').value == 'test-channel'

    @staticmethod
    def test_set_super_user_password(session_browser):
        """Test setting the super user password."""
        functional.set_app_form_value(session_browser, 'mumble',
                                      'id_super_user_password', 'testsu123')

    @staticmethod
    def test_set_join_password(session_browser):
        """Test setting join password."""
        functional.set_app_form_value(session_browser, 'mumble',
                                      'id_join_password', 'testjoin123')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test that backup and restore operations work on the app."""
        functional.set_app_form_value(session_browser, 'mumble',
                                      'id_root_channel_name', 'pre-backup')
        functional.backup_create(session_browser, self.app_name,
                                 'test_' + self.app_name)
        functional.set_app_form_value(session_browser, 'mumble',
                                      'id_root_channel_name', 'post-backup')
        functional.backup_restore(session_browser, self.app_name,
                                  'test_' + self.app_name)
        functional.nav_to_module(session_browser, 'mumble')
        assert session_browser.find_by_id(
            'id_root_channel_name').value == 'pre-backup'
        self.assert_app_running(session_browser)
