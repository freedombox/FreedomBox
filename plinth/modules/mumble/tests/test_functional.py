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

    # TODO: Improve test_backup_restore to actually check that data such
    # as rooms, identity or certificates are restored.

    def test_change_root_channel_name(self, session_browser):
        functional.app_enable(session_browser, 'mumble')
        functional.nav_to_module(session_browser, 'mumble')
        session_browser.find_by_id('id_root_channel_name').fill('testing123')
        functional.submit(session_browser, form_class='form-configuration')

        functional.nav_to_module(session_browser, 'mumble')
        assert session_browser.find_by_id(
            'id_root_channel_name').value == 'testing123'
