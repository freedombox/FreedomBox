#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os

from pytest import fixture
from pytest_bdd import given, parsers, then, when

from support import system

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


@given(parsers.parse('the default app is {app_name:w}'))
def set_default_app(browser, app_name):
    system.set_default_app(browser, app_name)


@given(parsers.parse('the domain name is set to {domain:S}'))
def set_domain_name(browser, domain):
    system.set_domain_name(browser, domain)


@when(parsers.parse('I change the hostname to {hostname:w}'))
def change_hostname_to(browser, hostname):
    system.set_hostname(browser, hostname)


@when(parsers.parse('I change the domain name to {domain:S}'))
def change_domain_name_to(browser, domain):
    system.set_domain_name(browser, domain)


@when(parsers.parse('I change the default app to {app_name:w}'))
def change_default_app_to(browser, app_name):
    system.set_default_app(browser, app_name)


@when('I change the language to <language>')
def change_language(browser, language):
    system.set_language(browser, language_codes[language])


@then(parsers.parse('the hostname should be {hostname:w}'))
def hostname_should_be(browser, hostname):
    assert system.get_hostname(browser) == hostname


@then(parsers.parse('the domain name should be {domain:S}'))
def domain_name_should_be(browser, domain):
    assert system.get_domain_name(browser) == domain


@then('Plinth language should be <language>')
def plinth_language_should_be(browser, language):
    assert system.check_language(browser, language_codes[language])


@given('the list of snapshots is empty')
def empty_snapshots_list(browser):
    system.delete_all_snapshots(browser)


@when('I manually create a snapshot')
def create_snapshot(browser):
    system.create_snapshot(browser)


@then(parsers.parse('there should be {count:d} snapshot in the list'))
def verify_snapshot_count(browser, count):
    num_snapshots = system.get_snapshot_count(browser)
    assert num_snapshots == count


@given(
    parsers.parse(
        'snapshots are configured with timeline snapshots '
        '{timeline_enabled:w}, software snapshots {software_enabled:w}, hourly '
        'limit {hourly:d}, daily limit {daily:d}, weekly limit {weekly:d}, '
        'monthly limit {monthly:d}, yearly limit {yearly:d}, delete old '
        'software snapshots {delete_old:d}'))
def snapshot_given_set_configuration(browser, timeline_enabled,
                                     software_enabled, hourly, daily, weekly,
                                     monthly, yearly, delete_old):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    system.snapshot_set_configuration(browser, timeline_enabled,
                                      software_enabled, hourly, daily, weekly,
                                      monthly, yearly, delete_old)


@when(
    parsers.parse(
        'I configure snapshots with timeline snapshots {timeline_enabled:w}, '
        'software snapshots {software_enabled:w}, hourly limit {hourly:d}, '
        'daily limit {daily:d}, weekly limit {weekly:d}, monthly limit '
        '{monthly:d}, yearly limit {yearly:d}, delete old software snapshots '
        '{delete_old:d}'))
def snapshot_set_configuration(browser, timeline_enabled, software_enabled,
                               hourly, daily, weekly, monthly, yearly,
                               delete_old):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    system.snapshot_set_configuration(browser, timeline_enabled,
                                      software_enabled, hourly, daily, weekly,
                                      monthly, yearly, delete_old)


@then(
    parsers.parse(
        'snapshots should be configured with timeline snapshots '
        '{timeline_enabled:w}, software snapshots {software_enabled:w}, hourly '
        'limit {hourly:d}, daily limit {daily:d}, weekly limit {weekly:d}, '
        'monthly limit {monthly:d}, yearly limit {yearly:d}, delete old '
        'software snapshots {delete_old:d}'))
def snapshot_assert_configuration(browser, timeline_enabled, software_enabled,
                                  hourly, daily, weekly, monthly, yearly,
                                  delete_old):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    assert (timeline_enabled, software_enabled, hourly, daily, weekly, monthly,
            yearly, delete_old) == system.snapshot_get_configuration(browser)


@then(parsers.parse('the default app should be {app_name:w}'))
def default_app_should_be(browser, app_name):
    assert system.check_home_page_redirect(browser, app_name)


@given('dynamicdns is configured')
def dynamicdns_configure(browser):
    system.dynamicdns_configure(browser)


@when('I change the dynamicdns configuration')
def dynamicdns_change_config(browser):
    system.dynamicdns_change_config(browser)


@then('dynamicdns should have the original configuration')
def dynamicdns_has_original_config(browser):
    assert system.dynamicdns_has_original_config(browser)


@when(parsers.parse('I create a backup of the {app_name:w} app data'))
def backup_create(browser, app_name):
    system.backup_create(browser, app_name)


@when(parsers.parse('I download the {app_name:w} app data backup'))
def backup_download(browser, app_name, downloaded_file_info):
    url = '/plinth/sys/backups/export-and-download/_functional_test_%s/' % \
        app_name
    file_path = system.download_file_logged_in(browser, url, app_name,
                                               suffix='.tar.gz')
    downloaded_file_info['path'] = file_path


@when(parsers.parse('I restore the {app_name:w} app data backup'))
def backup_restore(browser, app_name):
    system.backup_restore(browser, app_name)


@when(parsers.parse('I restore the downloaded {app_name:w} app data backup'))
def backup_restore_from_upload(browser, app_name, downloaded_file_info):
    path = downloaded_file_info["path"]
    try:
        system.backup_upload_and_restore(browser, app_name, path)
    except Exception as err:
        raise err
    finally:
        os.remove(path)


@given('pagekite is enabled')
def pagekite_is_enabled(browser):
    system.pagekite_enable(browser, True)


@given('pagekite is disabled')
def pagekite_is_disabled(browser):
    system.pagekite_enable(browser, False)


@when('I enable pagekite')
def pagekite_enable(browser):
    system.pagekite_enable(browser, True)


@when('I disable pagekite')
def pagekite_disable(browser):
    system.pagekite_enable(browser, False)


@then('pagekite should be enabled')
def pagekite_assert_enabled(browser):
    assert system.pagekite_is_enabled(browser)


@then('pagekite should be disabled')
def pagekite_assert_disabled(browser):
    assert not system.pagekite_is_enabled(browser)


@when(
    parsers.parse(
        'I configure pagekite with host {host:S}, port {port:d}, kite name {kite_name:S} and kite secret {kite_secret:w}'
    ))
def pagekite_configure(browser, host, port, kite_name, kite_secret):
    system.pagekite_configure(browser, host, port, kite_name, kite_secret)


@then(
    parsers.parse(
        'pagekite should be configured with host {host:S}, port {port:d}, kite name {kite_name:S} and kite secret {kite_secret:w}'
    ))
def pagekite_assert_configured(browser, host, port, kite_name, kite_secret):
    assert (host, port, kite_name,
            kite_secret) == system.pagekite_get_configuration(browser)


@given(parsers.parse('bind forwarders are set to {forwarders}'))
def bind_given_set_forwarders(browser, forwarders):
    system.bind_set_forwarders(browser, forwarders)


@when(parsers.parse('I set bind forwarders to {forwarders}'))
def bind_set_forwarders(browser, forwarders):
    system.bind_set_forwarders(browser, forwarders)


@then(parsers.parse('bind forwarders should be {forwarders}'))
def bind_assert_forwarders(browser, forwarders):
    assert system.bind_get_forwarders(browser) == forwarders


@given(parsers.parse('bind DNSSEC is {enable:w}'))
def bind_given_enable_dnssec(browser, enable):
    should_enable = (enable == 'enabled')
    system.bind_enable_dnssec(browser, should_enable)


@when(parsers.parse('I {enable:w} bind DNSSEC'))
def bind_enable_dnssec(browser, enable):
    should_enable = (enable == 'enable')
    system.bind_enable_dnssec(browser, should_enable)


@then(parsers.parse('bind DNSSEC should be {enabled:w}'))
def bind_assert_dnssec(browser, enabled):
    assert system.bind_get_dnssec(browser) == (enabled == 'enabled')


@given(parsers.parse('restricted console logins are {enabled}'))
def security_given_enable_restricted_logins(browser, enabled):
    should_enable = (enabled == 'enabled')
    system.security_enable_restricted_logins(browser, should_enable)


@when(parsers.parse('I {enable} restricted console logins'))
def security_enable_restricted_logins(browser, enable):
    should_enable = (enable == 'enable')
    system.security_enable_restricted_logins(browser, should_enable)


@then(parsers.parse('restricted console logins should be {enabled}'))
def security_assert_restricted_logins(browser, enabled):
    enabled = (enabled == 'enabled')
    assert system.security_get_restricted_logins(browser) == enabled


@given(parsers.parse('automatic upgrades are {enabled:w}'))
def upgrades_given_enable_automatic(browser, enabled):
    should_enable = (enabled == 'enabled')
    system.upgrades_enable_automatic(browser, should_enable)


@when(parsers.parse('I {enable:w} automatic upgrades'))
def upgrades_enable_automatic(browser, enable):
    should_enable = (enable == 'enable')
    system.upgrades_enable_automatic(browser, should_enable)


@then(parsers.parse('automatic upgrades should be {enabled:w}'))
def upgrades_assert_automatic(browser, enabled):
    should_be_enabled = (enabled == 'enabled')
    assert system.upgrades_get_automatic(browser) == should_be_enabled


@given(
    parsers.parse(
        'the {key_type:w} key for {domain:S} is imported in monkeysphere'))
def monkeysphere_given_import_key(browser, key_type, domain):
    system.monkeysphere_import_key(browser, key_type.lower(), domain)


@when(
    parsers.parse('I import {key_type:w} key for {domain:S} in monkeysphere'))
def monkeysphere_import_key(browser, key_type, domain):
    system.monkeysphere_import_key(browser, key_type.lower(), domain)


@then(
    parsers.parse(
        'the {key_type:w} key should imported for {domain:S} in monkeysphere'))
def monkeysphere_assert_imported_key(browser, key_type, domain):
    system.monkeysphere_assert_imported_key(browser, key_type.lower(), domain)


@then(
    parsers.parse('I should be able to publish {key_type:w} key for '
                  '{domain:S} in monkeysphere'))
def monkeysphere_publish_key(browser, key_type, domain):
    system.monkeysphere_publish_key(browser, key_type.lower(), domain)
