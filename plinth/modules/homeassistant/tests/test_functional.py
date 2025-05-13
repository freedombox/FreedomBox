# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for Home Assistant app."""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.homeassistant]


class TestHomeAssitantApp(functional.BaseAppTests):
    """Basic tests for Home Assistant app."""
    app_name = 'homeassistant'
    has_service = True
    has_web = False  # Can't yet check separate sub-domain
    diagnostics_delay = 5

    def install_and_setup(self, session_browser):
        """Set the domain to freedombox.local so that it can tested."""
        super().install_and_setup(session_browser)
        _domain_set(session_browser, 'freedombox.local')


def _domain_set(browser, domain):
    """Set the domain in the domain selection drop down."""
    functional.nav_to_module(browser, 'homeassistant')
    browser.select('domain_name', domain)
    functional.submit(browser, form_class='form-configuration')
