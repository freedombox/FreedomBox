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

from .interface import nav_to_module, submit

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
