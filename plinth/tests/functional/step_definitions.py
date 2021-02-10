# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Step definitions used across apps.
"""

import time

import pytest
from pytest_bdd import given, parsers, then, when

from plinth.tests import functional


@given("I'm a logged in user")
def logged_in(session_browser):
    functional.login(session_browser)


@given("I'm a logged out user")
def logged_out_user(session_browser):
    functional.visit(session_browser, '/plinth/accounts/logout/')


@when("I log out")
def log_out_user(session_browser):
    functional.visit(session_browser, '/plinth/accounts/logout/')


@given(parsers.parse('the {app_name:w} application is installed'))
def application_is_installed(session_browser, app_name):
    functional.install(session_browser, app_name)
    assert (functional.is_installed(session_browser, app_name))


@given(parsers.parse('the {app_name:w} application is enabled'))
def application_is_enabled(session_browser, app_name):
    functional.app_enable(session_browser, app_name)


@given(parsers.parse('the {app_name:w} application is disabled'))
def application_is_disabled(session_browser, app_name):
    functional.app_disable(session_browser, app_name)


@when(parsers.parse('I enable the {app_name:w} application'))
def enable_application(session_browser, app_name):
    functional.app_enable(session_browser, app_name)


@when(parsers.parse('I disable the {app_name:w} application'))
def disable_application(session_browser, app_name):
    functional.app_disable(session_browser, app_name)


@given(parsers.parse('the {app_name:w} application can be disabled'))
def app_can_be_disabled(session_browser, app_name):
    if not functional.app_can_be_disabled(session_browser, app_name):
        pytest.skip('network time application can\'t be disabled')


@then(parsers.parse('the {app_name:w} application is {enabled:w}'))
def app_assert_is_enabled(session_browser, app_name, enabled):
    assert enabled in ('enabled', 'disabled')
    enabled = (enabled == 'enabled')
    assert functional.app_is_enabled(session_browser, app_name) == enabled


@then(parsers.parse('the {service_name:w} service should be running'))
def service_should_be_running(session_browser, service_name):
    assert functional.eventually(functional.service_is_running,
                                 args=[session_browser, service_name])


@then(parsers.parse('the {service_name:w} service should not be running'))
def service_should_not_be_running(session_browser, service_name):
    assert functional.eventually(functional.service_is_not_running,
                                 args=[session_browser, service_name])


@then(parsers.parse('I should be prompted for login'))
def prompted_for_login(session_browser):
    assert functional.is_login_prompt(session_browser)


@given(parsers.parse('the domain name is set to {domain:S}'))
def step_set_domain_name(session_browser, domain):
    functional.set_domain_name(session_browser, domain)


@then(parsers.parse('the {site_name:w} site should be available'))
def site_should_be_available(session_browser, site_name):
    assert functional.is_available(session_browser, site_name)


@then(parsers.parse('the {site_name:w} site should not be available'))
def site_should_not_be_available(session_browser, site_name):
    assert not functional.is_available(session_browser, site_name)


@when(parsers.parse('I access {app_name:w} application'))
def access_application(session_browser, app_name):
    functional.access_url(session_browser, app_name)


@given('advanced mode is on')
def advanced_mode_is_on(session_browser):
    functional.set_advanced_mode(session_browser, True)


@when(
    parsers.parse('I create a backup of the {app_name:w} app data with '
                  'name {archive_name:w}'))
def backup_create(session_browser, app_name, archive_name):
    functional.backup_create(session_browser, app_name, archive_name)


@when(parsers.parse('I wait for {seconds} seconds'))
def sleep_for(seconds):
    seconds = int(seconds)
    time.sleep(seconds)


@when(
    parsers.parse(
        'I restore the {app_name:w} app data backup with name {archive_name:w}'
    ))
def backup_restore(session_browser, app_name, archive_name):
    functional.backup_restore(session_browser, app_name, archive_name)


@given(parsers.parse('the network device is in the {zone:w} firewall zone'))
def networks_set_firewall_zone(session_browser, zone):
    functional.networks_set_firewall_zone(session_browser, zone)


@given(
    parsers.parse('the domain name for {app_name:w} is set to {domain_name:S}')
)
def select_domain_name(session_browser, app_name, domain_name):
    functional.app_select_domain_name(session_browser, app_name, domain_name)


@then(parsers.parse('{app_name:w} app should be visible on the front page'))
def app_visible_on_front_page(session_browser, app_name):
    shortcuts = functional.find_on_front_page(session_browser, app_name)
    assert len(shortcuts) == 1


@then(parsers.parse('{app_name:w} app should not be visible on the front page')
      )
def app_not_visible_on_front_page(session_browser, app_name):
    shortcuts = functional.find_on_front_page(session_browser, app_name)
    assert len(shortcuts) == 0


@given(parsers.parse('bind forwarders are set to {forwarders}'))
def bind_given_set_forwarders(session_browser, forwarders):
    functional.set_forwarders(session_browser, forwarders)


@when(parsers.parse('I set bind forwarders to {forwarders}'))
def bind_set_forwarders(session_browser, forwarders):
    functional.set_forwarders(session_browser, forwarders)


@then(parsers.parse('bind forwarders should be {forwarders}'))
def bind_assert_forwarders(session_browser, forwarders):
    assert functional.get_forwarders(session_browser) == forwarders


@given(parsers.parse('the user {name:w} exists'))
def user_exists(session_browser, name):
    if functional.user_exists(session_browser, name):
        functional.delete_user(session_browser, name)
    functional.create_user(session_browser, name)


@given(parsers.parse('the user {name:w} in group {group:S} exists'))
def user_in_group_exists(session_browser, name, group):
    if functional.user_exists(session_browser, name):
        functional.delete_user(session_browser, name)
    functional.create_user(session_browser, name, groups=[group])


@given(parsers.parse("I'm logged in as the user {name:w}"))
@when(parsers.parse("I'm logged in as the user {name:w}"))
def logged_in_user(session_browser, name):
    functional.login_with_account(session_browser, functional.base_url, name)
