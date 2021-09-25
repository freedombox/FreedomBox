# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ejabberd app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.ejabberd]

# TODO Check service
# TODO Check domain name display


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'ejabberd')
    yield
    functional.app_disable(session_browser, 'ejabberd')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'ejabberd')

    functional.app_enable(session_browser, 'ejabberd')
    assert functional.service_is_running(session_browser, 'ejabberd')

    functional.app_disable(session_browser, 'ejabberd')
    assert functional.service_is_not_running(session_browser, 'ejabberd')


def test_message_archive_management(session_browser):
    """Test enabling message archive management."""
    functional.app_enable(session_browser, 'ejabberd')
    _enable_message_archive_management(session_browser)
    assert functional.service_is_running(session_browser, 'ejabberd')

    _disable_message_archive_management(session_browser)
    assert functional.service_is_running(session_browser, 'ejabberd')


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of app data."""
    functional.app_enable(session_browser, 'ejabberd')
    _jsxc_add_contact(session_browser)
    functional.backup_create(session_browser, 'ejabberd', 'test_ejabberd')

    _jsxc_delete_contact(session_browser)
    functional.backup_restore(session_browser, 'ejabberd', 'test_ejabberd')

    _jsxc_assert_has_contact(session_browser)


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
    functional.set_domain_name(browser, 'localhost')
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
