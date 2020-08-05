# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for bepasty app.
"""

from pytest_bdd import scenarios, then, when

from plinth.tests import functional

scenarios('bepasty.feature')

last_password_added = None


@when('I add a password')
def add_password(session_browser):
    global last_password_added
    _remove_all_passwords(session_browser)
    _add_password(session_browser)
    last_password_added = _get_password(session_browser)


@when('I remove all passwords')
def remove_all_passwords(session_browser):
    _remove_all_passwords(session_browser)


@then('I should be able to login to bepasty with that password')
def should_login(session_browser):
    assert _can_login(session_browser, last_password_added)


@then('I should not be able to login to bepasty with that password')
def should_not_login(session_browser):
    assert not _can_login(session_browser, last_password_added)


def _add_password(browser):
    functional.visit(browser, '/plinth/apps/bepasty/add')
    for permission in ['read', 'create', 'list', 'delete', 'admin']:
        browser.find_by_css('#id_bepasty-permissions input[value="{}"]'.format(
            permission)).check()
    browser.fill('bepasty-comment', 'bepasty functional test')
    functional.submit(browser, form_class='form-add')


def _remove_all_passwords(browser):
    functional.visit(browser, '/plinth/apps/bepasty')
    while True:
        remove_button = browser.find_by_css('.password-remove')
        if remove_button:
            functional.submit(browser, remove_button)
        else:
            break


def _get_password(browser):
    functional.visit(browser, '/plinth/apps/bepasty')
    return browser.find_by_css('.password-password').first.text


def _can_login(browser, password):
    functional.visit(browser, '/bepasty')
    logout = browser.find_by_value('Logout')
    if logout:
        logout.click()

    browser.fill('token', password)
    login = browser.find_by_xpath('//form//button')
    functional.submit(browser, login, '/bepasty')

    return bool(browser.find_by_value('Logout'))
