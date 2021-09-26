# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for monkeysphere app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.monkeysphere]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.set_advanced_mode(session_browser, True)
    functional.install(session_browser, 'monkeysphere')
    functional.set_domain_name(session_browser, 'mydomain.example')
    yield


def test_import_ssh_keys(session_browser):
    """Test importing SSH keys."""
    _import_key(session_browser, 'ssh', 'mydomain.example')
    _assert_imported_key(session_browser, 'ssh', 'mydomain.example')


def test_import_https_keys(session_browser):
    """Test importing HTTPS keys."""
    _import_key(session_browser, 'https', 'mydomain.example')
    _assert_imported_key(session_browser, 'https', 'mydomain.example')


def test_publish_ssh_keys(session_browser):
    """Test publishing SSH keys."""
    _import_key(session_browser, 'ssh', 'mydomain.example')
    _publish_key(session_browser, 'ssh', 'mydomain.example')


def test_publish_https_keys(session_browser):
    """Test publishing HTTPS keys."""
    _import_key(session_browser, 'https', 'mydomain.example')
    _publish_key(session_browser, 'https', 'mydomain.example')


def test_backup_restore(session_browser):
    """Test backup and restore of keys"""
    _import_key(session_browser, 'ssh', 'mydomain.example')
    _import_key(session_browser, 'https', 'mydomain.example')
    functional.backup_create(session_browser, 'monkeysphere',
                             'test_monkeysphere')

    functional.backup_restore(session_browser, 'monkeysphere',
                              'test_monkeysphere')
    _assert_imported_key(session_browser, 'ssh', 'mydomain.example')
    _assert_imported_key(session_browser, 'https', 'mydomain.example')


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
        _assert_imported_key(browser, key_type, domain)
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
