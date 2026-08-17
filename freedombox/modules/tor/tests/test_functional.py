# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for tor app.
"""

import pytest

from plinth.tests import functional

_TOR_FEATURE_TO_ELEMENT = {
    'relay': 'tor-relay_enabled',
    'bridge-relay': 'tor-bridge_relay_enabled',
    'hidden-services': 'tor-hs_enabled',
}

pytestmark = [pytest.mark.apps, pytest.mark.domain, pytest.mark.tor]


class TestTorApp(functional.BaseAppTests):
    app_name = 'tor'
    has_service = True
    has_web = False

    def test_set_tor_relay_configuration(self, session_browser):
        """Test setting Tor relay configuration."""
        functional.app_enable(session_browser, 'tor')
        _feature_enable(session_browser, 'relay', should_enable=False)
        _feature_enable(session_browser, 'relay', should_enable=True)
        _assert_feature_enabled(session_browser, 'relay', enabled=True)
        _assert_relay_port(session_browser, 'orport')

    def test_set_tor_bridge_relay_configuration(self, session_browser):
        """Test setting Tor bridge relay configuration."""
        functional.app_enable(session_browser, 'tor')
        _feature_enable(session_browser, 'bridge-relay', should_enable=False)
        _feature_enable(session_browser, 'bridge-relay', should_enable=True)
        _assert_feature_enabled(session_browser, 'bridge-relay', enabled=True)
        _assert_relay_port(session_browser, 'obfs3')
        _assert_relay_port(session_browser, 'obfs4')

    def test_set_tor_hidden_services_configuration(self, session_browser):
        """Test setting Tor hidden services configuration."""
        functional.app_enable(session_browser, 'tor')
        _feature_enable(session_browser, 'hidden-services',
                        should_enable=False)
        _feature_enable(session_browser, 'hidden-services', should_enable=True)
        _assert_feature_enabled(session_browser, 'hidden-services',
                                enabled=True)
        _assert_hidden_services(session_browser)

    # TODO: Test more thoroughly by checking same hidden service is restored
    # and by actually connecting using Tor.
    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of configuration."""
        functional.app_enable(session_browser, 'tor')
        _feature_enable(session_browser, 'relay', should_enable=True)
        _feature_enable(session_browser, 'bridge-relay', should_enable=True)
        _feature_enable(session_browser, 'hidden-services', should_enable=True)
        functional.backup_create(session_browser, 'tor', 'test_tor')

        _feature_enable(session_browser, 'relay', should_enable=False)
        _feature_enable(session_browser, 'hidden-services',
                        should_enable=False)
        functional.backup_restore(session_browser, 'tor', 'test_tor')

        assert functional.service_is_running(session_browser, 'tor')
        _assert_feature_enabled(session_browser, 'relay', enabled=True)
        _assert_feature_enabled(session_browser, 'bridge-relay', enabled=True)
        _assert_feature_enabled(session_browser, 'hidden-services',
                                enabled=True)


def _feature_enable(browser, feature, should_enable):
    """Enable/disable a Tor feature."""
    element_name = _TOR_FEATURE_TO_ELEMENT[feature]
    functional.nav_to_module(browser, 'tor')
    checkbox_element = browser.find_by_name(element_name).first
    if should_enable == checkbox_element.checked:
        return

    if should_enable:
        if feature == 'bridge-relay':
            browser.find_by_name('tor-relay_enabled').first.check()

        checkbox_element.check()
    else:
        checkbox_element.uncheck()

    functional.submit(browser, form_class='form-configuration')
    functional.wait_for_config_update(browser, 'tor')


def _assert_feature_enabled(browser, feature, enabled):
    """Assert whether Tor relay is enabled or disabled."""
    element_name = _TOR_FEATURE_TO_ELEMENT[feature]
    functional.nav_to_module(browser, 'tor')
    assert browser.find_by_name(element_name).first.checked == enabled


def _assert_relay_port(browser, port_name):
    """Assert that port is available in port forwarding info table."""
    functional.nav_to_module(browser, 'tor')
    assert f'tor-{port_name}' in [
        name.text for name in browser.find_by_css(
            '.table-port-forwarding-info td:first-child')
    ]


def _assert_hidden_services(browser):
    """Assert that hidden service information is shown."""
    functional.nav_to_module(browser, 'tor')
    assert browser.find_by_css('.tor-hs .tor-hs-hostname')
