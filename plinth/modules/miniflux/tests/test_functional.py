# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for Miniflux app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.miniflux]

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'str0ngp@$$word'
ADMIN_PASSWORD_NEW = 'str0ngERp@$$word'

CREDENTIALS = {'username': 'admin', 'password': ADMIN_PASSWORD}


class TestMinifluxApp(functional.BaseAppTests):
    """Class to customize basic app tests for Miniflux."""

    app_name = 'miniflux'
    has_service = True
    has_web = True

    @pytest.fixture(name='create_admin_user')
    def fixture_create_admin_user(self, session_browser):
        """Create an admin user for Miniflux."""
        functional.app_enable(session_browser, self.app_name)
        _create_admin_user(session_browser)

    def test_create_miniflux_admin_user(self, session_browser,
                                        create_admin_user):
        """Test creating an admin user."""
        _miniflux_login(session_browser)
        # Verify that this user can see admin settings
        with functional.wait_for_page_update(session_browser):
            session_browser.links.find_by_href(
                '/miniflux/settings').first.click()

        assert not session_browser.links.find_by_href(
            '/miniflux/users').is_empty()

    def test_reset_miniflux_user_password(self, session_browser,
                                          create_admin_user):
        """Test Miniflux user password reset."""
        CREDENTIALS['password'] = ADMIN_PASSWORD_NEW
        _reset_user_password(session_browser)
        _miniflux_login(session_browser)
        assert not session_browser.links.find_by_href(
            '/miniflux/unread').is_empty()

    @pytest.mark.backups
    def test_backup_restore(self, session_browser, create_admin_user):
        """Test backup and restore of app data."""
        _subscribe(session_browser, 'https://planet.debian.org/atom.xml')
        super().test_backup_restore(session_browser)
        assert _is_subscribed(session_browser, 'Planet Debian')


def _fill_credentials_form(browser, href):
    """Fill the user credentials form in Miniflux app."""
    functional.nav_to_module(browser, 'miniflux')
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href(
            f'/plinth/apps/miniflux/{href}/').first.click()

    browser.fill('miniflux-username', CREDENTIALS['username'])
    browser.fill('miniflux-password', CREDENTIALS['password'])
    browser.fill('miniflux-password_confirmation', CREDENTIALS['password'])
    functional.submit(browser, form_class='form-miniflux')


def _create_admin_user(browser):
    """Create Miniflux admin user."""
    _fill_credentials_form(browser, 'create-admin-user')


def _open_miniflux_app(browser):
    """Load the web interface of Miniflux."""
    functional.visit(browser, '/miniflux/')
    main = browser.find_by_id('main')
    functional.eventually(lambda: main.visible)


def _miniflux_logout(browser):
    """Attempt to log out of Miniflux app. Doesn't fail if not logged in."""
    _open_miniflux_app(browser)
    maybe_logout_button = browser.links.find_by_href('/miniflux/logout')
    if not maybe_logout_button.is_empty():
        with functional.wait_for_page_update(browser):
            maybe_logout_button.first.click()


def _miniflux_submit(browser):
    """Perform the Submit action in Miniflux forms."""
    functional.submit(browser,
                      element=browser.find_by_css('button[type="submit"]'))


def _miniflux_login(browser):
    """Login to miniflux with the given credentials."""
    _open_miniflux_app(browser)
    _miniflux_logout(browser)
    browser.find_by_id('form-username').fill(CREDENTIALS['username'])
    browser.find_by_id('form-password').fill(CREDENTIALS['password'])
    _miniflux_submit(browser)


def _reset_user_password(browser):
    """Reset a Miniflux user's password from FreedomBox web interface."""
    _fill_credentials_form(browser, 'reset-user-password')


def _subscribe(browser, feed_url):
    """Subscribe to a feed in Miniflux."""
    _open_miniflux_app(browser)
    _miniflux_login(browser)
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href('/miniflux/subscribe').first.click()

    with functional.wait_for_page_update(browser):
        browser.find_by_id('form-url').fill(feed_url)
        _miniflux_submit(browser)


def _is_subscribed(browser, feed_name):
    """Check if the user is subscribed to a feed."""
    _open_miniflux_app(browser)
    _miniflux_login(browser)
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href('/miniflux/feeds').first.click()

    return browser.is_text_present(feed_name)
