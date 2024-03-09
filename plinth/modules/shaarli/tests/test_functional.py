# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for shaarli app.
"""

import time

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.shaarli]


class TestShaarliApp(functional.BaseAppTests):
    app_name = 'shaarli'
    has_service = False
    has_web = True

    def install_and_setup(self, session_browser):
        """Install the app and set it up if needed."""
        super().install_and_setup(session_browser)
        self._shaarli_is_setup(session_browser)

    def _shaarli_is_setup(self, session_browser):
        """Finish shaarli installation by creating user."""
        functional.access_url(session_browser, self.app_name)
        if not session_browser.url.endswith('/shaarli/install'):
            # Setup has already been completed.
            return

        username_field = session_browser.find_by_id('username')
        username_field.fill(functional.config['DEFAULT']['username'])

        password_field = session_browser.find_by_id('password')
        password_field.fill(functional.config['DEFAULT']['password'])

        button = session_browser.find_by_css(
            '#installform input[type=submit]')[0]
        functional.submit(session_browser, element=button)

    def _shaarli_login(self, session_browser):
        """Login to shaarli."""
        functional.access_url(session_browser, 'shaarli/login')

        login_form = session_browser.find_by_id('login-form')
        if not login_form:
            return

        login_field = login_form.find_by_name('login')
        login_field.fill(functional.config['DEFAULT']['username'])

        password_field = login_form.find_by_name('password')
        password_field.fill(functional.config['DEFAULT']['password'])

        login_form.find_by_css('input[type=submit]').click()

    def test_add_bookmark(self, session_browser):
        """Test adding a bookmark."""
        self._shaarli_login(session_browser)
        functional.access_url(session_browser, 'shaarli/admin/add-shaare')

        addlink_form = session_browser.find_by_id('addlink-form')
        addlink_form.find_by_id('shaare').fill('https://freedombox.org/')
        addlink_form.find_by_css('input[type=submit]').click()

        time.sleep(2)
        session_browser.find_by_id('button-save-edit').click()

        links = session_browser.links.find_by_href('https://freedombox.org/')
        assert len(links) > 0

    # TODO: Test deleting bookmarks.

    def test_uninstall(self, session_browser):
        """After uninstall test, after installing run initial setup."""
        super().test_uninstall(session_browser)
        self._shaarli_is_setup(session_browser)
