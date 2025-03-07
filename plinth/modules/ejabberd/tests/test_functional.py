# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for ejabberd app."""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.ejabberd]

# TODO Check domain name displayed in description


class TestEjabberdApp(functional.BaseAppTests):
    app_name = 'ejabberd'
    has_service = True
    has_web = False

    @pytest.fixture(scope='module', autouse=True)
    def fixture_background(self, session_browser):
        """Login, install, and enable the app."""
        functional.login(session_browser)
        functional.install(session_browser, 'jsxc')
        functional.install(session_browser, self.app_name)
        functional.app_enable(session_browser, 'jsxc')
        functional.app_enable(session_browser, self.app_name)
        yield
        functional.login(session_browser)
        functional.app_disable(session_browser, self.app_name)

    def test_add_remove_domain(self, session_browser):
        """Test adding and removing a domain."""
        functional.app_enable(session_browser, 'ejabberd')
        functional.app_enable(session_browser, 'avahi')
        functional.set_hostname(session_browser, 'freedombox')
        _enable_domain(session_browser, 'freedombox.local')

        _disable_domain(session_browser, 'freedombox.local')
        assert not _is_domain_enabled(session_browser, 'freedombox.local')
        assert functional.service_is_running(session_browser, 'ejabberd')

        _enable_domain(session_browser, 'freedombox.local')
        assert _is_domain_enabled(session_browser, 'freedombox.local')
        assert functional.service_is_running(session_browser, 'ejabberd')

    def test_message_archive_management(self, session_browser):
        """Test enabling message archive management."""
        functional.app_enable(session_browser, 'ejabberd')
        _enable_message_archive_management(session_browser)
        assert functional.service_is_running(session_browser, 'ejabberd')

        _disable_message_archive_management(session_browser)
        assert functional.service_is_running(session_browser, 'ejabberd')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of app data."""
        functional.app_enable(session_browser, 'ejabberd')
        functional.app_enable(session_browser, 'jsxc')
        _jsxc_add_contact(session_browser)
        functional.backup_create(session_browser, 'ejabberd', 'test_ejabberd')

        _jsxc_delete_contact(session_browser)
        functional.backup_restore(session_browser, 'ejabberd', 'test_ejabberd')

        _jsxc_assert_has_contact(session_browser)


def _enable_domain(browser, domain):
    """Add domain name to Ejabberd configuration."""
    functional.nav_to_module(browser, 'ejabberd')
    checkbox = browser.find_by_value(domain).first
    checkbox.check()
    functional.submit(browser, form_class='form-configuration')


def _disable_domain(browser, domain):
    """Remove domain name from Ejabberd configuration."""
    functional.nav_to_module(browser, 'ejabberd')
    checkbox = browser.find_by_value(domain).first
    checkbox.uncheck()
    functional.submit(browser, form_class='form-configuration')


def _is_domain_enabled(browser, domain):
    """Return whether the domain name is enabled."""
    functional.nav_to_module(browser, 'ejabberd')
    checkbox = browser.find_by_value(domain).first
    return checkbox.checked


def _enable_message_archive_management(browser):
    """Enable Message Archive Management in Ejabberd."""
    functional.nav_to_module(browser, 'ejabberd')
    functional.change_checkbox_status(browser, 'ejabberd', 'id_MAM_enabled',
                                      'enabled')


def _disable_message_archive_management(browser):
    """Enable Message Archive Management in Ejabberd."""
    functional.nav_to_module(browser, 'ejabberd')
    functional.change_checkbox_status(browser, 'ejabberd', 'id_MAM_enabled',
                                      'disabled')


def _is_jsxc_buddy_list_loaded(browser):
    """Return whether the jsxc buddy list has been loaded."""
    if browser.find_by_text('new contact'):
        # no contacts
        return True

    buddy_list = browser.find_by_id('jsxc_buddylist').first
    contacts = buddy_list.find_by_css('.jsxc_rosteritem')

    return len(contacts) > 0


def _jsxc_login(browser):
    """Login to JSXC."""
    username = functional.config['DEFAULT']['username']
    password = functional.config['DEFAULT']['password']
    functional.visit(browser, '/plinth/apps/jsxc/jsxc/')
    assert functional.eventually(browser.find_by_text,
                                 ['BOSH Server reachable.'])
    if browser.find_by_text('relogin'):
        browser.reload()

    browser.find_by_id('jsxc-username').fill(username)
    browser.find_by_id('jsxc-password').fill(password)
    browser.find_by_id('jsxc-submit').click()
    assert functional.eventually(browser.find_by_css,
                                 ['#jsxc_roster.jsxc_state_shown'])


def _jsxc_add_contact(browser):
    """Add a contact to JSXC user's roster."""
    # Configure a static domain
    functional.domain_add(browser, 'mydomain.example')
    functional.install(browser, 'jsxc')
    _jsxc_login(browser)
    functional.eventually(_is_jsxc_buddy_list_loaded, args=[browser])
    new = browser.find_by_text('new contact')
    if new:  # roster is empty
        new.first.click()
        browser.find_by_id('jsxc_username').fill('alice@localhost')
        browser.find_by_text('Add').first.click()
        assert functional.eventually(browser.find_by_text, ['alice@localhost'])


def _jsxc_delete_contact(browser):
    """Delete the contact from JSXC user's roster."""
    _jsxc_login(browser)

    # noqa, pylint: disable=unnecessary-lambda
    functional.eventually(browser.find_by_css, ['div.jsxc_more'])
    browser.find_by_css('div.jsxc_more').first.click()
    functional.eventually(browser.find_by_text, ['delete contact'])
    browser.find_by_text('delete contact').first.click()
    functional.eventually(browser.find_by_text, ['Remove'])
    browser.find_by_text('Remove').first.click()


def _jsxc_assert_has_contact(browser):
    """Check whether the contact is in JSXC user's roster."""
    _jsxc_login(browser)
    assert functional.eventually(browser.find_by_text, ['alice@localhost'])
