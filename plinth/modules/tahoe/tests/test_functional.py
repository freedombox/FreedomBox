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


class TestTahoeApp(functional.BaseAppTests):
    app_name = 'tahoe'
    has_service = True
    has_web = True

    @pytest.fixture(scope='class', autouse=True)
    def fixture_setup(self, session_browser):
        """Setup the app."""
        functional.login(session_browser)
        functional.set_advanced_mode(session_browser, True)
        functional.set_domain_name(session_browser, 'mydomain.example')
        functional.install(session_browser, self.app_name)
        functional.app_select_domain_name(session_browser, self.app_name,
                                          'mydomain.example')

    def test_default_introducers(self, session_browser):
        """Test default introducers."""
        assert _get_introducer(session_browser, 'mydomain.example', 'local')
        assert _get_introducer(session_browser, 'mydomain.example',
                               'connected')

    def test_add_remove_introducers(self, session_browser):
        """Test add and remove introducers."""
        if _get_introducer(session_browser, 'anotherdomain.example',
                           'connected'):
            _remove_introducer(session_browser, 'anotherdomain.example')

        _add_introducer(session_browser, 'anotherdomain.example')
        assert _get_introducer(session_browser, 'anotherdomain.example',
                               'connected')

        _remove_introducer(session_browser, 'anotherdomain.example')
        assert not _get_introducer(session_browser, 'anotherdomain.example',
                                   'connected')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of app data."""
        if not _get_introducer(session_browser, 'backupdomain.example',
                               'connected'):
            _add_introducer(session_browser, 'backupdomain.example')
        functional.backup_create(session_browser, self.app_name, 'test_tahoe')

        _remove_introducer(session_browser, 'backupdomain.example')
        functional.backup_restore(session_browser, self.app_name, 'test_tahoe')

        assert functional.service_is_running(session_browser, self.app_name)
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
