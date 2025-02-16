# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for matrixsynapse app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.matrixsynapse]


class TestMatrixSynapseApp(functional.BaseAppTests):
    app_name = 'matrixsynapse'
    has_service = True
    has_web = False
    diagnostics_delay = 1

    @pytest.fixture(scope='class', autouse=True)
    def fixture_setup(self, session_browser):
        """Setup the app."""
        functional.login(session_browser)
        functional.domain_add(session_browser, 'mydomain.example')

    def install_and_setup(self, session_browser):
        """Install the app and run setup."""
        super().install_and_setup(session_browser)
        functional.app_select_domain_name(session_browser, self.app_name,
                                          'mydomain.example')

    def test_uninstall(self, session_browser):
        """After uninstall test, after installing select the domain again."""
        super().test_uninstall(session_browser)
        functional.app_select_domain_name(session_browser, self.app_name,
                                          'mydomain.example')
