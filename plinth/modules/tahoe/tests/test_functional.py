# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for tahoe app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.tahoe, pytest.mark.skip]

# TODO: When tahoe-lafs is restarted, it leaves a .gnupg folder in
# /var/lib/tahoe-lafs and failes to start in the next run. Enable tests after
# this is fixed.


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.set_advanced_mode(session_browser, True)
    functional.set_domain_name(session_browser, 'mydomain.example')
    functional.install(session_browser, 'tahoe')
    functional.app_select_domain_name(session_browser, 'tahoe',
                                      'mydomain.example')
    yield
    functional.app_disable(session_browser, 'tahoe')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'tahoe')

    functional.app_enable(session_browser, 'tahoe')
    assert functional.service_is_running(session_browser, 'tahoe')

    functional.app_disable(session_browser, 'tahoe')
    assert functional.service_is_not_running(session_browser, 'tahoe')


def test_default_introducers(session_browser):
    """Test default introducers."""
    functional.app_enable(session_browser, 'tahoe')
    assert _get_introducer(session_browser, 'mydomain.example', 'local')
    assert _get_introducer(session_browser, 'mydomain.example', 'connected')


def test_add_remove_introducers(session_browser):
    """Test add and remove introducers."""
    functional.app_enable(session_browser, 'tahoe')
    if _get_introducer(session_browser, 'anotherdomain.example', 'connected'):
        _remove_introducer(session_browser, 'anotherdomain.example')

    _add_introducer(session_browser, 'anotherdomain.example')
    assert _get_introducer(session_browser, 'anotherdomain.example',
                           'connected')

    _remove_introducer(session_browser, 'anotherdomain.example')
    assert not _get_introducer(session_browser, 'anotherdomain.example',
                               'connected')


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of app data."""
    functional.app_enable(session_browser, 'tahoe')
    if not _get_introducer(session_browser, 'backupdomain.example',
                           'connected'):
        _add_introducer(session_browser, 'backupdomain.example')
    functional.backup_create(session_browser, 'tahoe', 'test_tahoe')

    _remove_introducer(session_browser, 'backupdomain.example')
    functional.backup_restore(session_browser, 'tahoe', 'test_tahoe')

    assert functional.service_is_running(session_browser, 'tahoe')
    assert _get_introducer(session_browser, 'backupdomain.example',
                           'connected')


def _get_introducer(browser, domain, introducer_type):
    """Return an introducer element with a given type from tahoe-lafs."""
    functional.nav_to_module(browser, 'tahoe')
    css_class = '.{}-introducers .introducer-furl'.format(introducer_type)
    for furl in browser.find_by_css(css_class):
        if domain in furl.text:
            return furl.parent

    return None


def _add_introducer(browser, domain):
    """Add a new introducer into tahoe-lafs."""
    functional.nav_to_module(browser, 'tahoe')

    furl = 'pb://ewe4zdz6kxn7xhuvc7izj2da2gpbgeir@tcp:{}:3456/' \
           'fko4ivfwgqvybppwar3uehkx6spaaou7'.format(domain)
    browser.fill('pet_name', 'testintroducer')
    browser.fill('furl', furl)
    functional.submit(browser, form_class='form-add-introducer')


def _remove_introducer(browser, domain):
    """Remove an introducer from tahoe-lafs."""
    introducer = _get_introducer(browser, domain, 'connected')
    functional.submit(browser, element=introducer.find_by_css('.form-remove'))
