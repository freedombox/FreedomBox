# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for Tor Proxy app.
"""

import pytest

from plinth.tests import functional

_TOR_FEATURE_TO_ELEMENT = {'software': 'torproxy-apt_transport_tor_enabled'}

pytestmark = [pytest.mark.apps, pytest.mark.torproxy]


class TestTorProxyApp(functional.BaseAppTests):
    """Tests for the Tor Proxy app."""
    app_name = 'torproxy'
    has_service = True
    has_web = False
    # TODO: Investigate why accessing IPv6 sites through Tor fails in
    # container.
    check_diagnostics = False

    def test_set_download_software_packages_over_tor(self, session_browser):
        """Test setting download software packages over Tor."""
        functional.app_enable(session_browser, 'torproxy')
        _feature_enable(session_browser, 'software', should_enable=True)
        _feature_enable(session_browser, 'software', should_enable=False)
        _assert_feature_enabled(session_browser, 'software', enabled=False)

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of configuration."""
        functional.app_enable(session_browser, 'torproxy')
        # TODO: Check that upstream bridges are restored.
        functional.backup_create(session_browser, 'torproxy', 'test_torproxy')

        functional.backup_restore(session_browser, 'torproxy', 'test_torproxy')

        assert functional.service_is_running(session_browser, 'torproxy')


def _feature_enable(browser, feature, should_enable):
    """Enable/disable a Tor Proxy feature."""
    element_name = _TOR_FEATURE_TO_ELEMENT[feature]
    functional.nav_to_module(browser, 'torproxy')
    checkbox_element = browser.find_by_name(element_name).first
    if should_enable == checkbox_element.checked:
        return

    if should_enable:
        checkbox_element.check()
    else:
        checkbox_element.uncheck()

    functional.submit(browser, form_class='form-configuration')
    functional.wait_for_config_update(browser, 'torproxy')


def _assert_feature_enabled(browser, feature, enabled):
    """Assert whether Tor Proxy feature is enabled or disabled."""
    element_name = _TOR_FEATURE_TO_ELEMENT[feature]
    functional.nav_to_module(browser, 'torproxy')
    assert browser.find_by_name(element_name).first.checked == enabled
