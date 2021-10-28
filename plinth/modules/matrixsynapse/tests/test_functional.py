# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for matrixsynapse app.
"""

import pytest
import time

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.matrixsynapse]


class TestMatrixSynapseApp(functional.BaseAppTests):
    app_name = 'matrixsynapse'
    has_service = True
    has_web = False

    @pytest.fixture(scope='class', autouse=True)
    def fixture_background(self, session_browser):
        """Login and install the app."""
        functional.login(session_browser)
        functional.set_domain_name(session_browser, 'mydomain.example')
        functional.install(session_browser, self.app_name)
        functional.app_select_domain_name(session_browser, self.app_name,
                                          'mydomain.example')
        yield
        functional.app_disable(session_browser, self.app_name)

    def test_run_diagnostics(self, session_browser):
        """Add a short delay before checking diagnostics."""
        functional.app_enable(session_browser, self.app_name)
        time.sleep(1)
        super().test_run_diagnostics(session_browser)
