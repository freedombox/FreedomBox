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


@given(parsers.parse('the default app is {app_name:w}'))
def set_default_app(browser, app_name):
    system.set_default_app(browser, app_name)


@given(parsers.parse('the domain name is set to {domain:w}'))
def set_domain_name(browser, domain):
    system.set_domain_name(browser, domain)


@when(parsers.parse('I change the hostname to {hostname:w}'))
def change_hostname_to(browser, hostname):
    system.set_hostname(browser, hostname)


@when(parsers.parse('I change the domain name to {domain:w}'))
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


@then(parsers.parse('the domain name should be {domain:w}'))
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


@then(parsers.parse('the default app should be {app_name:w}'))
def default_app_should_be(browser, app_name):
    assert system.check_home_page_redirect(browser, app_name)
