# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for bind app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.bind]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'bind')
    yield
    functional.app_disable(session_browser, 'bind')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'bind')

    functional.app_enable(session_browser, 'bind')
    assert functional.service_is_running(session_browser, 'bind')

    functional.app_disable(session_browser, 'bind')
    assert functional.service_is_not_running(session_browser, 'bind')


def test_set_forwarders(session_browser):
    """Test setting forwarders."""
    functional.app_enable(session_browser, 'bind')
    functional.set_forwarders(session_browser, '1.1.1.1')

    functional.set_forwarders(session_browser, '1.1.1.1 1.0.0.1')
    assert functional.get_forwarders(session_browser) == '1.1.1.1 1.0.0.1'


def test_enable_disable_dnssec(session_browser):
    """Test enabling/disabling DNSSEC."""
    functional.app_enable(session_browser, 'bind')
    _enable_dnssec(session_browser, False)

    _enable_dnssec(session_browser, True)
    assert _get_dnssec(session_browser)

    _enable_dnssec(session_browser, False)
    assert not _get_dnssec(session_browser)


@pytest.mark.backups
def test_backup(session_browser):
    """Test backup and restore."""
    functional.app_enable(session_browser, 'bind')
    functional.set_forwarders(session_browser, '1.1.1.1')
    _enable_dnssec(session_browser, False)
    functional.backup_create(session_browser, 'bind', 'test_bind')

    functional.set_forwarders(session_browser, '1.0.0.1')
    _enable_dnssec(session_browser, True)

    functional.backup_restore(session_browser, 'bind', 'test_bind')
    assert functional.get_forwarders(session_browser) == '1.1.1.1'
    assert not _get_dnssec(session_browser)


def _enable_dnssec(browser, enable):
    """Enable/disable DNSSEC in bind configuration."""
    functional.nav_to_module(browser, 'bind')
    if enable:
        browser.check('enable_dnssec')
    else:
        browser.uncheck('enable_dnssec')

    functional.submit(browser, form_class='form-configuration')


def _get_dnssec(browser):
    """Return whether DNSSEC is enabled/disabled in bind configuration."""
    functional.nav_to_module(browser, 'bind')
    return browser.find_by_name('enable_dnssec').first.checked
