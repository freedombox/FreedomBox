# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for radicale app.
"""

import logging

import pytest
import requests

from plinth.tests import functional

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.apps, pytest.mark.radicale]


class TestRadicaleApp(functional.BaseAppTests):
    app_name = 'radicale'
    has_service = True
    has_web = True

    def assert_app_running(self, session_browser):
        """Assert that the app is running."""
        assert functional.service_is_running(session_browser, self.app_name)
        assert _calendar_is_available(session_browser)
        assert _addressbook_is_available(session_browser)

    def assert_app_not_running(self, session_browser):
        """Assert that the app is not running."""
        assert functional.service_is_not_running(session_browser,
                                                 self.app_name)
        assert not _calendar_is_available(session_browser)
        assert not _addressbook_is_available(session_browser)

    def test_access_rights(self, session_browser):
        """Test setting the access rights."""
        functional.app_enable(session_browser, 'radicale')
        _set_access_rights(session_browser, 'owner_only')

        # Owner-write access rights
        _set_access_rights(session_browser, 'owner_write')
        assert functional.service_is_running(session_browser, 'radicale')
        assert _get_access_rights(session_browser) == 'owner_write'

        # Authenticated access rights
        _set_access_rights(session_browser, 'authenticated')
        assert functional.service_is_running(session_browser, 'radicale')
        assert _get_access_rights(session_browser) == 'authenticated'

        # Owner-only access rights
        _set_access_rights(session_browser, 'owner_only')
        assert functional.service_is_running(session_browser, 'radicale')
        assert _get_access_rights(session_browser) == 'owner_only'

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of configuration."""
        functional.app_enable(session_browser, 'radicale')
        _set_access_rights(session_browser, 'owner_only')
        functional.backup_create(session_browser, 'radicale', 'test_radicale')

        _set_access_rights(session_browser, 'owner_write')
        functional.backup_restore(session_browser, 'radicale', 'test_radicale')

        assert functional.service_is_running(session_browser, 'radicale')
        assert _get_access_rights(session_browser) == 'owner_only'


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
