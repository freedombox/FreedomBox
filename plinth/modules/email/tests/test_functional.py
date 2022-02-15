# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for email app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.email]


class TestEmailApp(functional.BaseAppTests):
    app_name = 'email'
    has_service = True
    has_web = False
    check_diagnostics = True

    @pytest.fixture(autouse=True)
    def fixture_background(self, session_browser):
        functional.login(session_browser)
        functional.set_advanced_mode(session_browser, True)
        functional.install(session_browser, self.app_name)
        functional.app_enable(session_browser, self.app_name)
        yield
        functional.login(session_browser)
        functional.app_disable(session_browser, self.app_name)
