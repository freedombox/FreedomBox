# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for bepasty app.
"""

from pytest_bdd import given, scenarios, then, when

from plinth.tests import functional

scenarios('bepasty.feature')

last_password_added = None


@given('I am not logged in to bepasty')
def not_logged_in(session_browser):
    _logout(session_browser)


@when('I set the default permissions to Read files')
def set_default_permissions_read(session_browser):
    _set_default_permissions(session_browser, 'read')


@when('I set the default permissions to List and read all files')
def set_default_permissions_list_read(session_browser):
    _set_default_permissions(session_browser, 'read list')


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


@then('I should be able to List all Items in bepasty')
def should_list_all(session_browser):
    assert _can_list_all(session_browser)


@then('I should not be able to List all Items in bepasty')
def should_not_list_all(session_browser):
    assert _cannot_list_all(session_browser)


def _set_default_permissions(browser, permissions=''):
    functional.nav_to_module(browser, 'bepasty')
    browser.choose('default_permissions', permissions)
    functional.submit(browser, form_class='form-configuration')


def _add_password(browser):
    functional.visit(browser, '/plinth/apps/bepasty/add')
    for permission in ['read', 'create', 'list', 'delete', 'admin']:
        browser.find_by_css('#id_bepasty-permissions input[value="{}"]'.format(
            permission)).check()
    browser.fill('bepasty-comment', 'bepasty functional test')
    functional.submit(browser, form_class='form-add')


def _remove_all_passwords(browser):
    functional.nav_to_module(browser, 'bepasty')
    while True:
        remove_button = browser.find_by_css('.password-remove')
        if remove_button:
            functional.submit(browser, remove_button)
        else:
            break


def _get_password(browser):
    functional.nav_to_module(browser, 'bepasty')
    return browser.find_by_css('.password-password').first.text


def _can_login(browser, password):
    _logout(browser)
    browser.fill('token', password)
    login = browser.find_by_xpath('//form//button')
    functional.submit(browser, login, '/bepasty')

    return bool(browser.find_by_value('Logout'))


def _logout(browser):
    functional.visit(browser, '/bepasty')
    logout = browser.find_by_value('Logout')
    if logout:
        logout.click()


def _can_list_all(browser):
    functional.visit(browser, '/bepasty')
    return functional.eventually(browser.links.find_by_href,
                                 ['/bepasty/+list'], 5)


def _cannot_list_all(browser):
    functional.visit(browser, '/bepasty/+list')
    return functional.eventually(browser.is_text_present, ['Forbidden'], 5)
