# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import time

from pytest import fixture
from pytest_bdd import given, parsers, then, when

from support import config, system

language_codes = {
    'Deutsch': 'de',
    'Nederlands': 'nl',
    'Português': 'pt',
    'Türkçe': 'tr',
    'dansk': 'da',
    'español': 'es',
    'français': 'fr',
    'norsk (bokmål)': 'nb',
    'polski': 'pl',
    'svenska': 'sv',
    'Русский': 'ru',
    'తెలుగు': 'te',
    '简体中文': 'zh-hans'
}


@fixture(scope='session')
def downloaded_file_info():
    return dict()


@given(parsers.parse('the home page is {app_name:w}'))
def set_home_page(session_browser, app_name):
    system.set_home_page(session_browser, app_name)


@given(parsers.parse('the domain name is set to {domain:S}'))
def set_domain_name(session_browser, domain):
    system.set_domain_name(session_browser, domain)


@given('advanced mode is on')
def advanced_mode_is_on(session_browser):
    system.set_advanced_mode(session_browser, True)


@when(parsers.parse('I change the hostname to {hostname:w}'))
def change_hostname_to(session_browser, hostname):
    system.set_hostname(session_browser, hostname)


@when(parsers.parse('I change the domain name to {domain:S}'))
def change_domain_name_to(session_browser, domain):
    system.set_domain_name(session_browser, domain)


@when(parsers.parse('I change the home page to {app_name:w}'))
def change_home_page_to(session_browser, app_name):
    system.set_home_page(session_browser, app_name)


@when('I change the language to <language>')
def change_language(session_browser, language):
    system.set_language(session_browser, language_codes[language])


@then(parsers.parse('the hostname should be {hostname:w}'))
def hostname_should_be(session_browser, hostname):
    assert system.get_hostname(session_browser) == hostname


@then(parsers.parse('the domain name should be {domain:S}'))
def domain_name_should_be(session_browser, domain):
    assert system.get_domain_name(session_browser) == domain


@then('Plinth language should be <language>')
def plinth_language_should_be(session_browser, language):
    assert system.check_language(session_browser, language_codes[language])


@given('the list of snapshots is empty')
def empty_snapshots_list(session_browser):
    system.delete_all_snapshots(session_browser)


@when('I manually create a snapshot')
def create_snapshot(session_browser):
    system.create_snapshot(session_browser)


@then(parsers.parse('there should be {count:d} snapshot in the list'))
def verify_snapshot_count(session_browser, count):
    num_snapshots = system.get_snapshot_count(session_browser)
    assert num_snapshots == count


@given(
    parsers.parse(
        'snapshots are configured with free space {free_space:d}, timeline '
        'snapshots {timeline_enabled:w}, software snapshots '
        '{software_enabled:w}, hourly limit {hourly:d}, daily limit {daily:d}'
        ', weekly limit {weekly:d}, monthly limit {monthly:d}, yearly limit '
        '{yearly:d}'))
def snapshot_given_set_configuration(session_browser, free_space,
                                     timeline_enabled, software_enabled,
                                     hourly, daily, weekly, monthly, yearly):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    system.snapshot_set_configuration(session_browser, free_space,
                                      timeline_enabled, software_enabled,
                                      hourly, daily, weekly, monthly, yearly)


@when(
    parsers.parse(
        'I configure snapshots with free space {free_space:d}, '
        'timeline snapshots {timeline_enabled:w}, '
        'software snapshots {software_enabled:w}, hourly limit {hourly:d}, '
        'daily limit {daily:d}, weekly limit {weekly:d}, monthly limit '
        '{monthly:d}, yearly limit {yearly:d}'))
def snapshot_set_configuration(session_browser, free_space, timeline_enabled,
                               software_enabled, hourly, daily, weekly,
                               monthly, yearly):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    system.snapshot_set_configuration(session_browser, free_space,
                                      timeline_enabled, software_enabled,
                                      hourly, daily, weekly, monthly, yearly)


@then(
    parsers.parse(
        'snapshots should be configured with free space {free_space:d}, '
        'timeline snapshots {timeline_enabled:w}, software snapshots '
        '{software_enabled:w}, hourly limit {hourly:d}, daily limit '
        '{daily:d}, weekly limit {weekly:d}, monthly limit {monthly:d}, '
        'yearly limit {yearly:d}'))
def snapshot_assert_configuration(session_browser, free_space,
                                  timeline_enabled, software_enabled, hourly,
                                  daily, weekly, monthly, yearly):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    assert (free_space, timeline_enabled, software_enabled, hourly, daily,
            weekly, monthly,
            yearly) == system.snapshot_get_configuration(session_browser)


@then(parsers.parse('the home page should be {app_name:w}'))
def home_page_should_be(session_browser, app_name):
    assert system.check_home_page_redirect(session_browser, app_name)


@given('dynamicdns is configured')
def dynamicdns_configure(session_browser):
    system.dynamicdns_configure(session_browser)


@when('I change the dynamicdns configuration')
def dynamicdns_change_config(session_browser):
    system.dynamicdns_change_config(session_browser)


@then('dynamicdns should have the original configuration')
def dynamicdns_has_original_config(session_browser):
    assert system.dynamicdns_has_original_config(session_browser)


@when(parsers.parse('I create a backup of the {app_name:w} app data'))
def backup_create(session_browser, app_name):
    if config.getboolean('DEFAULT', 'delete_root_backup_archives'):
        system.backup_delete_root_archives(session_browser)
    system.backup_create(session_browser, app_name)


@when(parsers.parse('I download the latest app data backup'))
def backup_download(session_browser, downloaded_file_info):
    file_path = system.download_latest_backup(session_browser)
    downloaded_file_info['path'] = file_path


@when(parsers.parse('I restore the {app_name:w} app data backup'))
def backup_restore(session_browser, app_name):
    system.backup_restore(session_browser, app_name)


@when(parsers.parse('I restore the downloaded app data backup'))
def backup_restore_from_upload(session_browser, app_name,
                               downloaded_file_info):
    path = downloaded_file_info["path"]
    try:
        system.backup_upload_and_restore(session_browser, app_name, path)
    except Exception as err:
        raise err
    finally:
        os.remove(path)


@then('pagekite should be enabled')
def pagekite_assert_enabled(session_browser):
    assert system.pagekite_is_enabled(session_browser)


@then('pagekite should be disabled')
def pagekite_assert_disabled(session_browser):
    assert not system.pagekite_is_enabled(session_browser)


@when(
    parsers.parse(
        'I configure pagekite with host {host:S}, port {port:d}, kite name {kite_name:S} and kite secret {kite_secret:w}'
    ))
def pagekite_configure(session_browser, host, port, kite_name, kite_secret):
    system.pagekite_configure(session_browser, host, port, kite_name,
                              kite_secret)


@then(
    parsers.parse(
        'pagekite should be configured with host {host:S}, port {port:d}, kite name {kite_name:S} and kite secret {kite_secret:w}'
    ))
def pagekite_assert_configured(session_browser, host, port, kite_name,
                               kite_secret):
    assert (host, port, kite_name,
            kite_secret) == system.pagekite_get_configuration(session_browser)


@given(parsers.parse('bind forwarders are set to {forwarders}'))
def bind_given_set_forwarders(session_browser, forwarders):
    system.bind_set_forwarders(session_browser, forwarders)


@when(parsers.parse('I set bind forwarders to {forwarders}'))
def bind_set_forwarders(session_browser, forwarders):
    system.bind_set_forwarders(session_browser, forwarders)


@then(parsers.parse('bind forwarders should be {forwarders}'))
def bind_assert_forwarders(session_browser, forwarders):
    assert system.bind_get_forwarders(session_browser) == forwarders


@given(parsers.parse('bind DNSSEC is {enable:w}'))
def bind_given_enable_dnssec(session_browser, enable):
    should_enable = (enable == 'enabled')
    system.bind_enable_dnssec(session_browser, should_enable)


@when(parsers.parse('I {enable:w} bind DNSSEC'))
def bind_enable_dnssec(session_browser, enable):
    should_enable = (enable == 'enable')
    system.bind_enable_dnssec(session_browser, should_enable)


@then(parsers.parse('bind DNSSEC should be {enabled:w}'))
def bind_assert_dnssec(session_browser, enabled):
    assert system.bind_get_dnssec(session_browser) == (enabled == 'enabled')


@given(parsers.parse('restricted console logins are {enabled}'))
def security_given_enable_restricted_logins(session_browser, enabled):
    should_enable = (enabled == 'enabled')
    system.security_enable_restricted_logins(session_browser, should_enable)


@when(parsers.parse('I {enable} restricted console logins'))
def security_enable_restricted_logins(session_browser, enable):
    should_enable = (enable == 'enable')
    system.security_enable_restricted_logins(session_browser, should_enable)


@then(parsers.parse('restricted console logins should be {enabled}'))
def security_assert_restricted_logins(session_browser, enabled):
    enabled = (enabled == 'enabled')
    assert system.security_get_restricted_logins(session_browser) == enabled


@given(parsers.parse('automatic upgrades are {enabled:w}'))
def upgrades_given_enable_automatic(session_browser, enabled):
    should_enable = (enabled == 'enabled')
    system.upgrades_enable_automatic(session_browser, should_enable)


@when(parsers.parse('I {enable:w} automatic upgrades'))
def upgrades_enable_automatic(session_browser, enable):
    should_enable = (enable == 'enable')
    system.upgrades_enable_automatic(session_browser, should_enable)


@then(parsers.parse('automatic upgrades should be {enabled:w}'))
def upgrades_assert_automatic(session_browser, enabled):
    should_be_enabled = (enabled == 'enabled')
    assert system.upgrades_get_automatic(session_browser) == should_be_enabled


@given(
    parsers.parse(
        'the {key_type:w} key for {domain:S} is imported in monkeysphere'))
def monkeysphere_given_import_key(session_browser, key_type, domain):
    system.monkeysphere_import_key(session_browser, key_type.lower(), domain)


@when(parsers.parse('I import {key_type:w} key for {domain:S} in monkeysphere')
      )
def monkeysphere_import_key(session_browser, key_type, domain):
    system.monkeysphere_import_key(session_browser, key_type.lower(), domain)


@then(
    parsers.parse(
        'the {key_type:w} key should imported for {domain:S} in monkeysphere'))
def monkeysphere_assert_imported_key(session_browser, key_type, domain):
    system.monkeysphere_assert_imported_key(session_browser, key_type.lower(),
                                            domain)


@then(
    parsers.parse('I should be able to publish {key_type:w} key for '
                  '{domain:S} in monkeysphere'))
def monkeysphere_publish_key(session_browser, key_type, domain):
    system.monkeysphere_publish_key(session_browser, key_type.lower(), domain)


@when(parsers.parse('I wait for {seconds} seconds'))
def sleep_for(seconds):
    seconds = int(seconds)
    time.sleep(seconds)


@when(parsers.parse('I open the main page'))
def open_main_page(session_browser):
    system.open_main_page(session_browser)


@then(parsers.parse('the main page should be shown'))
def main_page_is_shown(session_browser):
    assert (session_browser.url.endswith('/plinth/'))


@given(parsers.parse('the network device is in the {zone:w} firewall zone'))
def networks_set_firewall_zone(session_browser, zone):
    system.networks_set_firewall_zone(session_browser, zone)


@then('the root disk should be shown')
def storage_root_disk_is_shown(session_browser):
    assert system.storage_is_root_disk_shown(session_browser)
