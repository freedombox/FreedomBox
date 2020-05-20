# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for monkeysphere app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('monkeysphere.feature')


@given(
    parsers.parse(
        'the {key_type:w} key for {domain:S} is imported in monkeysphere'))
def monkeysphere_given_import_key(session_browser, key_type, domain):
    _import_key(session_browser, key_type.lower(), domain)


@when(parsers.parse('I import {key_type:w} key for {domain:S} in monkeysphere')
      )
def monkeysphere_import_key(session_browser, key_type, domain):
    _import_key(session_browser, key_type.lower(), domain)


@then(
    parsers.parse(
        'the {key_type:w} key should imported for {domain:S} in monkeysphere'))
def monkeysphere_assert_imported_key(session_browser, key_type, domain):
    _assert_imported_key(session_browser, key_type.lower(), domain)


@then(
    parsers.parse('I should be able to publish {key_type:w} key for '
                  '{domain:S} in monkeysphere'))
def monkeysphere_publish_key(session_browser, key_type, domain):
    _publish_key(session_browser, key_type.lower(), domain)


def _find_domain(browser, key_type, domain_type, domain):
    """Iterate every domain of a given type which given key type."""
    keys_of_type = browser.find_by_css(
        '.monkeysphere-service-{}'.format(key_type))
    for key_of_type in keys_of_type:
        search_domains = key_of_type.find_by_css(
            '.monkeysphere-{}-domain'.format(domain_type))
        for search_domain in search_domains:
            if search_domain.text == domain:
                return key_of_type, search_domain

    raise IndexError('Domain not found')


def _import_key(browser, key_type, domain):
    """Import a key of specified type for given domain into monkeysphere."""
    try:
        monkeysphere_assert_imported_key(browser, key_type, domain)
    except IndexError:
        pass
    else:
        return

    key, _ = _find_domain(browser, key_type, 'importable', domain)
    with functional.wait_for_page_update(browser):
        key.find_by_css('.button-import').click()


def _assert_imported_key(browser, key_type, domain):
    """Assert that a key of specified type for given domain was imported.."""
    functional.nav_to_module(browser, 'monkeysphere')
    return _find_domain(browser, key_type, 'imported', domain)


def _publish_key(browser, key_type, domain):
    """Publish a key of specified type for given domain from monkeysphere."""
    functional.nav_to_module(browser, 'monkeysphere')
    key, _ = _find_domain(browser, key_type, 'imported', domain)
    with functional.wait_for_page_update(browser):
        key.find_by_css('.button-publish').click()

    functional.wait_for_config_update(browser, 'monkeysphere')
