# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for SOGo app."""

import time

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.sogo]


class TestSOGoApp(functional.BaseAppTests):
    """Basic tests for the SOGo app."""
    app_name = 'sogo'
    has_service = True
    disable_after_tests = False

    def test_login(self, session_browser):
        """Test that login to SOGo interface works."""
        _login(session_browser)
        assert functional.eventually(_is_logged_in, [session_browser])


def _login(browser) -> None:
    """Login to SOGo web interface."""
    functional.visit(browser, '/SOGo/')
    username = functional.config['DEFAULT']['username']
    password = functional.config['DEFAULT']['password']
    functional.eventually(browser.find_by_id, ['input_1'])
    time.sleep(1)  # For some reason, waiting does not work
    browser.find_by_id('input_1').fill(username)
    browser.find_by_id('passwordField').fill(password)
    submit = browser.find_by_css(
        'form[name=loginForm] button[type=submit]').first
    functional.submit(browser, element=submit)


def _is_logged_in(browser) -> bool:
    """Return whether SOGo login was successful."""
    logout = browser.find_by_css('a[href="../logoff"]')
    return bool(logout)
