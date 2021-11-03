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

    @pytest.fixture(scope='class', autouse=True)
    def fixture_setup(self, session_browser):
        """Setup the app."""
        functional.login(session_browser)
        functional.install(session_browser, self.app_name)
        self._zoph_is_setup(session_browser)

    def _zoph_is_setup(self, session_browser):
        """Click setup button on the setup page."""
        functional.nav_to_module(session_browser, self.app_name)
        button = session_browser.find_by_css('input[name="zoph_setup"]')
        if button:
            functional.submit(session_browser, element=button)

    def assert_app_running(self, session_browser):
        assert functional.app_is_enabled(session_browser, self.app_name)

    def assert_app_not_running(self, session_browser):
        assert not functional.app_is_enabled(session_browser, self.app_name)
