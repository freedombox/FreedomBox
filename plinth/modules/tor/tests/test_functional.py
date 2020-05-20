# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for tor app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

_TOR_FEATURE_TO_ELEMENT = {
    'relay': 'tor-relay_enabled',
    'bridge-relay': 'tor-bridge_relay_enabled',
    'hidden-services': 'tor-hs_enabled',
    'software': 'tor-apt_transport_tor_enabled'
}

scenarios('tor.feature')


@given(parsers.parse('tor relay is {enabled:w}'))
def tor_given_relay_enable(session_browser, enabled):
    _feature_enable(session_browser, 'relay', enabled)


@when(parsers.parse('I {enable:w} tor relay'))
def tor_relay_enable(session_browser, enable):
    _feature_enable(session_browser, 'relay', enable)


@then(parsers.parse('tor relay should be {enabled:w}'))
def tor_assert_relay_enabled(session_browser, enabled):
    _assert_feature_enabled(session_browser, 'relay', enabled)


@then(parsers.parse('tor {port_name:w} port should be displayed'))
def tor_assert_port_displayed(session_browser, port_name):
    assert port_name in _get_relay_ports(session_browser)


@given(parsers.parse('tor bridge relay is {enabled:w}'))
def tor_given_bridge_relay_enable(session_browser, enabled):
    _feature_enable(session_browser, 'bridge-relay', enabled)


@when(parsers.parse('I {enable:w} tor bridge relay'))
def tor_bridge_relay_enable(session_browser, enable):
    _feature_enable(session_browser, 'bridge-relay', enable)


@then(parsers.parse('tor bridge relay should be {enabled:w}'))
def tor_assert_bridge_relay_enabled(session_browser, enabled):
    _assert_feature_enabled(session_browser, 'bridge-relay', enabled)


@given(parsers.parse('tor hidden services are {enabled:w}'))
def tor_given_hidden_services_enable(session_browser, enabled):
    _feature_enable(session_browser, 'hidden-services', enabled)


@when(parsers.parse('I {enable:w} tor hidden services'))
def tor_hidden_services_enable(session_browser, enable):
    _feature_enable(session_browser, 'hidden-services', enable)


@then(parsers.parse('tor hidden services should be {enabled:w}'))
def tor_assert_hidden_services_enabled(session_browser, enabled):
    _assert_feature_enabled(session_browser, 'hidden-services', enabled)


@then(parsers.parse('tor hidden services information should be displayed'))
def tor_assert_hidden_services(session_browser):
    _assert_hidden_services(session_browser)


@given(parsers.parse('download software packages over tor is {enabled:w}'))
def tor_given_download_software_over_tor_enable(session_browser, enabled):
    _feature_enable(session_browser, 'software', enabled)


@when(parsers.parse('I {enable:w} download software packages over tor'))
def tor_download_software_over_tor_enable(session_browser, enable):
    _feature_enable(session_browser, 'software', enable)


@then(
    parsers.parse('download software packages over tor should be {enabled:w}'))
def tor_assert_download_software_over_tor(session_browser, enabled):
    _assert_feature_enabled(session_browser, 'software', enabled)


def _feature_enable(browser, feature, should_enable):
    """Enable/disable a Tor feature."""
    if not isinstance(should_enable, bool):
        should_enable = should_enable in ('enable', 'enabled')

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
    if not isinstance(enabled, bool):
        enabled = enabled in ('enable', 'enabled')

    element_name = _TOR_FEATURE_TO_ELEMENT[feature]
    functional.nav_to_module(browser, 'tor')
    assert browser.find_by_name(element_name).first.checked == enabled


def _get_relay_ports(browser):
    """Return the list of ports shown in the relay table."""
    functional.nav_to_module(browser, 'tor')
    return [
        port_name.text
        for port_name in browser.find_by_css('.tor-relay-port-name')
    ]


def _assert_hidden_services(browser):
    """Assert that hidden service information is shown."""
    functional.nav_to_module(browser, 'tor')
    assert browser.find_by_css('.tor-hs .tor-hs-hostname')
