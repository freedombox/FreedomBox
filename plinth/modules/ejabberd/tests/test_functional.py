# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ejabberd app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('ejabberd.feature')


@given('I have added a contact to my roster')
def ejabberd_add_contact(session_browser):
    _jsxc_add_contact(session_browser)


@when('I delete the contact from my roster')
def ejabberd_delete_contact(session_browser):
    _jsxc_delete_contact(session_browser)


@then('I should have a contact on my roster')
def ejabberd_should_have_contact(session_browser):
    _jsxc_assert_has_contact(session_browser)


@when(parsers.parse('I enable message archive management'))
def ejabberd_enable_archive_management(session_browser):
    _enable_message_archive_management(session_browser)


@when(parsers.parse('I disable message archive management'))
def ejabberd_disable_archive_management(session_browser):
    _disable_message_archive_management(session_browser)


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
