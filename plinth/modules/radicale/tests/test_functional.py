# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for radicale app.
"""

import logging

import requests
from pytest_bdd import given, scenarios, then, when

from plinth.tests import functional

logger = logging.getLogger(__name__)
scenarios('radicale.feature')


@given('the access rights are set to "only the owner can view or make changes"'
       )
def radicale_given_owner_only(session_browser):
    _set_access_rights(session_browser, 'owner_only')


@given('the access rights are set to "any user can view, but only the '
       'owner can make changes"')
def radicale_given_owner_write(session_browser):
    _set_access_rights(session_browser, 'owner_write')


@given('the access rights are set to "any user can view or make changes"')
def radicale_given_authenticated(session_browser):
    _set_access_rights(session_browser, 'authenticated')


@when('I change the access rights to "only the owner can view or make changes"'
      )
def radicale_set_owner_only(session_browser):
    _set_access_rights(session_browser, 'owner_only')


@when('I change the access rights to "any user can view, but only the '
      'owner can make changes"')
def radicale_set_owner_write(session_browser):
    _set_access_rights(session_browser, 'owner_write')


@when('I change the access rights to "any user can view or make changes"')
def radicale_set_authenticated(session_browser):
    _set_access_rights(session_browser, 'authenticated')


@then('the access rights should be "only the owner can view or make changes"')
def radicale_check_owner_only(session_browser):
    assert _get_access_rights(session_browser) == 'owner_only'


@then('the access rights should be "any user can view, but only the '
      'owner can make changes"')
def radicale_check_owner_write(session_browser):
    assert _get_access_rights(session_browser) == 'owner_write'


@then('the access rights should be "any user can view or make changes"')
def radicale_check_authenticated(session_browser):
    assert _get_access_rights(session_browser) == 'authenticated'


@then('the calendar should be available')
def assert_calendar_is_available(session_browser):
    assert _calendar_is_available(session_browser)


@then('the calendar should not be available')
def assert_calendar_is_not_available(session_browser):
    assert not _calendar_is_available(session_browser)


@then('the addressbook should be available')
def assert_addressbook_is_available(session_browser):
    assert _addressbook_is_available(session_browser)


@then('the addressbook should not be available')
def assert_addressbook_is_not_available(session_browser):
    assert not _addressbook_is_available(session_browser)


def _get_access_rights(browser):
    access_rights_types = ['owner_only', 'owner_write', 'authenticated']
    functional.nav_to_module(browser, 'radicale')
    for access_rights_type in access_rights_types:
        if browser.find_by_value(access_rights_type).checked:
            return access_rights_type


def _set_access_rights(browser, access_rights_type):
    functional.nav_to_module(browser, 'radicale')
    browser.choose('access_rights', access_rights_type)
    functional.submit(browser, form_class='form-configuration')


def _calendar_is_available(browser):
    """Return whether calendar is available at well-known URL."""
    conf = functional.config['DEFAULT']
    url = functional.base_url + '/.well-known/caldav'
    logging.captureWarnings(True)
    request = requests.get(url, auth=(conf['username'], conf['password']),
                           verify=False)
    logging.captureWarnings(False)
    return request.status_code != 404


def _addressbook_is_available(browser):
    """Return whether addressbook is available at well-known URL."""
    conf = functional.config['DEFAULT']
    url = functional.base_url + '/.well-known/carddav'
    logging.captureWarnings(True)
    request = requests.get(url, auth=(conf['username'], conf['password']),
                           verify=False)
    logging.captureWarnings(False)
    return request.status_code != 404
