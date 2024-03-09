# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for zoph app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.zoph]


class TestZophApp(functional.BaseAppTests):
    app_name = 'zoph'
    has_service = False
    has_web = True

    def install_and_setup(self, session_browser):
        """Install the app and run setup."""
        super().install_and_setup(session_browser)
        self._zoph_is_setup(session_browser)

    def _zoph_is_setup(self, session_browser):
        """Click setup button on the setup page."""
        functional.nav_to_module(session_browser, self.app_name)
        if session_browser.find_by_css('.form-configuration'):
            functional.submit(session_browser, form_class='form-configuration')

    def assert_app_running(self, session_browser):
        assert functional.app_is_enabled(session_browser, self.app_name)

    def assert_app_not_running(self, session_browser):
        assert not functional.app_is_enabled(session_browser, self.app_name)
