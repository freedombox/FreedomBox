# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for bepasty app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.bepasty]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'bepasty')
    yield
    functional.app_disable(session_browser, 'bepasty')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'bepasty')

    functional.app_enable(session_browser, 'bepasty')
    assert functional.is_available(session_browser, 'bepasty')

    functional.app_disable(session_browser, 'bepasty')
    assert not functional.is_available(session_browser, 'bepasty')


def test_set_default_permissions_list_and_read_all(session_browser):
    functional.app_enable(session_browser, 'bepasty')
    _logout(session_browser)
    _set_default_permissions(session_browser, 'read list')

    assert _can_list_all(session_browser)


def test_set_default_permissions_read_files(session_browser):
    functional.app_enable(session_browser, 'bepasty')
    _logout(session_browser)
    _set_default_permissions(session_browser, 'read')

    assert _cannot_list_all(session_browser)


def test_add_password(session_browser):
    functional.app_enable(session_browser, 'bepasty')
    password_added = _add_and_save_password(session_browser)

    assert _can_login(session_browser, password_added)


def test_remove_password(session_browser):
    functional.app_enable(session_browser, 'bepasty')
    password_added = _add_and_save_password(session_browser)
    _remove_all_passwords(session_browser)

    assert not _can_login(session_browser, password_added)


@pytest.mark.backups
def test_backup_and_restore(session_browser):
    functional.app_enable(session_browser, 'bepasty')
    password_added = _add_and_save_password(session_browser)
    functional.backup_create(session_browser, 'bepasty', 'test_bepasty')

    _remove_all_passwords(session_browser)
    functional.backup_restore(session_browser, 'bepasty', 'test_bepasty')

    assert functional.is_available(session_browser, 'bepasty')
    assert _can_login(session_browser, password_added)


def _add_and_save_password(session_browser):
    _remove_all_passwords(session_browser)
    _add_password(session_browser)
    return _get_password(session_browser)


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
