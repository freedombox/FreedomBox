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

from support import config

from .interface import default_url, nav_to_module, submit

config_page_title_language_map = {
    'da': 'Generel Konfiguration',
    'de': 'Allgemeine Konfiguration',
    'es': 'Configuración general',
    'fr': 'Configuration générale',
    'nb': 'Generelt oppsett',
    'nl': 'Algemene Instellingen',
    'pl': 'Ustawienia główne',
    'pt': 'Configuração Geral',
    'ru': 'Общие настройки',
    'sv': 'Allmän Konfiguration',
    'te': 'సాధారణ ఆకృతీకరణ',
    'tr': 'Genel Yapılandırma',
    'zh-hans': '常规配置',
}


def get_hostname(browser):
    nav_to_module(browser, 'config')
    return browser.find_by_id('id_configuration-hostname').value


def set_hostname(browser, hostname):
    nav_to_module(browser, 'config')
    browser.find_by_id('id_configuration-hostname').fill(hostname)
    submit(browser)


def get_domain_name(browser):
    nav_to_module(browser, 'config')
    return browser.find_by_id('id_configuration-domainname').value


def set_domain_name(browser, domain_name):
    nav_to_module(browser, 'config')
    browser.find_by_id('id_configuration-domainname').fill(domain_name)
    submit(browser)


def set_default_app(browser, app_name):
    nav_to_module(browser, 'config')
    drop_down = browser.find_by_id('id_configuration-defaultapp')
    drop_down.select(app_name)
    submit(browser)


def set_language(browser, language_code):
    username = config['DEFAULT']['username']
    browser.visit(config['DEFAULT']['url'] +
                  '/plinth/sys/users/{}/edit/'.format(username))
    browser.find_by_xpath('//select[@id="id_language"]//option[@value="' +
                          language_code + '"]').first.click()
    submit(browser)


def check_language(browser, language_code):
    nav_to_module(browser, 'config')
    return browser.title == config_page_title_language_map[language_code]


def delete_all_snapshots(browser):
    browser.visit(config['DEFAULT']['url'] + '/plinth/sys/snapshot/all/delete')
    submit(browser)


def create_snapshot(browser):
    browser.visit(config['DEFAULT']['url'] + '/plinth/sys/snapshot/manage/')
    submit(browser)  # Click on 'Create Snapshot'


def get_snapshot_count(browser):
    browser.visit(config['DEFAULT']['url'] + '/plinth/sys/snapshot/manage/')
    # Subtract 1 for table header
    return len(browser.find_by_xpath('//tr')) - 1


def check_home_page_redirect(browser, app_name):
    browser.visit(config['DEFAULT']['url'])
    return browser.find_by_xpath(
        "//a[contains(@href, '/plinth/') and @title='FreedomBox']")


def dynamicdns_configure(browser):
    nav_to_module(browser, 'dynamicdns')
    browser.find_link_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    browser.find_by_id('id_enabled').check()
    browser.find_by_id('id_service_type').select('GnuDIP')
    browser.find_by_id('id_dynamicdns_server').fill('example.com')
    browser.find_by_id('id_dynamicdns_domain').fill('freedombox.example.com')
    browser.find_by_id('id_dynamicdns_user').fill('tester')
    browser.find_by_id('id_dynamicdns_secret').fill('testingtesting')
    browser.find_by_id('id_dynamicdns_ipurl').fill(
        'http://myip.datasystems24.de')
    submit(browser)


def dynamicdns_has_original_config(browser):
    nav_to_module(browser, 'dynamicdns')
    browser.find_link_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    enabled = browser.find_by_id('id_enabled').value
    service_type = browser.find_by_id('id_service_type').value
    server = browser.find_by_id('id_dynamicdns_server').value
    domain = browser.find_by_id('id_dynamicdns_domain').value
    user = browser.find_by_id('id_dynamicdns_user').value
    ipurl = browser.find_by_id('id_dynamicdns_ipurl').value
    if enabled and service_type == 'GnuDIP' and server == 'example.com' \
       and domain == 'freedombox.example.com' and user == 'tester' \
       and ipurl == 'http://myip.datasystems24.de':
        return True
    else:
        return False


def dynamicdns_change_config(browser):
    nav_to_module(browser, 'dynamicdns')
    browser.find_link_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    browser.find_by_id('id_enabled').check()
    browser.find_by_id('id_service_type').select('GnuDIP')
    browser.find_by_id('id_dynamicdns_server').fill('2.example.com')
    browser.find_by_id('id_dynamicdns_domain').fill('freedombox2.example.com')
    browser.find_by_id('id_dynamicdns_user').fill('tester2')
    browser.find_by_id('id_dynamicdns_secret').fill('testingtesting2')
    browser.find_by_id('id_dynamicdns_ipurl').fill(
        'http://myip2.datasystems24.de')
    submit(browser)


def backup_create(browser, app_name):
    browser.visit(default_url)
    nav_to_module(browser, 'backups')
    delete = browser.find_link_by_href(
        '/plinth/sys/backups/delete/_functional_test_' + app_name + '/')
    if delete:
        delete.first.click()
        submit(browser)

    browser.find_link_by_href('/plinth/sys/backups/create/').first.click()
    browser.find_by_id('id_backups-name').fill('_functional_test_' + app_name)
    submit(browser)


def backup_export(browser, app_name):
    browser.visit(default_url)
    nav_to_module(browser, 'backups')
    browser.find_link_by_href(
        '/plinth/sys/backups/export/_functional_test_'
        + app_name + '/').first.click()
    browser.find_by_id('id_backups-disk_0').first.check()
    submit(browser)


def backup_restore(browser, app_name):
    browser.visit(default_url)
    nav_to_module(browser, 'backups')
    browser.find_link_by_href(
        '/plinth/sys/backups/restore/Root%2520Filesystem/_functional_test_'
        + app_name + '.tar.gz/').first.click()
    submit(browser)
