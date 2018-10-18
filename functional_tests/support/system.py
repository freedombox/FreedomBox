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

from support import application, config

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


def snapshot_set_configuration(browser, timeline_enabled, software_enabled,
                               hourly, daily, weekly, monthly, yearly,
                               delete_old):
    """Set the configuration for snapshots."""
    nav_to_module(browser, 'snapshot')
    browser.find_by_name('enable_timeline_snapshots').select(
        'yes' if timeline_enabled else 'no')
    browser.find_by_name('enable_software_snapshots').select(
        'yes' if software_enabled else 'no')
    browser.find_by_name('hourly_limit').fill(hourly)
    browser.find_by_name('daily_limit').fill(daily)
    browser.find_by_name('weekly_limit').fill(weekly)
    browser.find_by_name('monthly_limit').fill(monthly)
    browser.find_by_name('yearly_limit').fill(yearly)
    browser.find_by_name('number_min_age').fill(delete_old)
    submit(browser)


def snapshot_get_configuration(browser):
    """Return the current configuration for snapshots."""
    nav_to_module(browser, 'snapshot')
    return (browser.find_by_name('enable_timeline_snapshots').value == 'yes',
            browser.find_by_name('enable_software_snapshots').value == 'yes',
            int(browser.find_by_name('hourly_limit').value),
            int(browser.find_by_name('daily_limit').value),
            int(browser.find_by_name('weekly_limit').value),
            int(browser.find_by_name('monthly_limit').value),
            int(browser.find_by_name('yearly_limit').value),
            int(browser.find_by_name('number_min_age').value))


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
    application.install(browser, 'backups')
    delete = browser.find_link_by_href(
        '/plinth/sys/backups/delete/_functional_test_' + app_name + '/')
    if delete:
        delete.first.click()
        submit(browser)

    browser.find_link_by_href('/plinth/sys/backups/create/').first.click()
    browser.find_by_id('id_backups-name').fill('_functional_test_' + app_name)
    for app in browser.find_by_css('input[type=checkbox]'):
        app.uncheck()

    browser.find_by_value(app_name).first.check()
    submit(browser)


def backup_export(browser, app_name):
    browser.visit(default_url)
    nav_to_module(browser, 'backups')
    browser.find_link_by_href('/plinth/sys/backups/export/_functional_test_' +
                              app_name + '/').first.click()
    browser.find_by_id('id_backups-disk_0').first.check()
    submit(browser)


def backup_restore(browser, app_name):
    browser.visit(default_url)
    nav_to_module(browser, 'backups')
    browser.find_link_by_href(
        '/plinth/sys/backups/restore/Root%2520Filesystem/_functional_test_' +
        app_name + '.tar.gz/').first.click()
    submit(browser)


def pagekite_enable(browser, should_enable):
    """Enable/disable pagekite service."""
    nav_to_module(browser, 'pagekite')
    browser.find_link_by_href('/plinth/sys/pagekite/configure/').first.click()
    checkbox = browser.find_by_id('id_pagekite-enabled').first
    if checkbox.checked == should_enable:
        return

    if should_enable:
        checkbox.check()
    else:
        checkbox.uncheck()

    submit(browser)


def pagekite_is_enabled(browser):
    """Return whether pagekite is enabled."""
    nav_to_module(browser, 'pagekite')
    browser.find_link_by_href('/plinth/sys/pagekite/configure/').first.click()
    return browser.find_by_id('id_pagekite-enabled').checked


def pagekite_configure(browser, host, port, kite_name, kite_secret):
    """Configure pagekite basic parameters."""
    nav_to_module(browser, 'pagekite')
    browser.find_link_by_href('/plinth/sys/pagekite/configure/').first.click()
    #time.sleep(0.250)  # Wait for 200ms show animation to complete
    browser.fill('pagekite-server_domain', host)
    browser.fill('pagekite-server_port', str(port))
    browser.fill('pagekite-kite_name', kite_name)
    browser.fill('pagekite-kite_secret', kite_secret)
    submit(browser)


def pagekite_get_configuration(browser):
    """Return pagekite basic parameters."""
    nav_to_module(browser, 'pagekite')
    browser.find_link_by_href('/plinth/sys/pagekite/configure/').first.click()
    return (browser.find_by_name('pagekite-server_domain').value,
            int(browser.find_by_name('pagekite-server_port').value),
            browser.find_by_name('pagekite-kite_name').value,
            browser.find_by_name('pagekite-kite_secret').value)


def bind_set_forwarders(browser, forwarders):
    """Set the forwarders list (space separated) in bind configuration."""
    nav_to_module(browser, 'bind')
    browser.fill('forwarders', forwarders)
    submit(browser, form_class='form-configuration')


def bind_get_forwarders(browser):
    """Return the forwarders list (space separated) in bind configuration."""
    nav_to_module(browser, 'bind')
    return browser.find_by_name('forwarders').first.value


def bind_enable_dnssec(browser, enable):
    """Enable/disable DNSSEC in bind configuration."""
    nav_to_module(browser, 'bind')
    if enable:
        browser.check('enable_dnssec')
    else:
        browser.uncheck('enable_dnssec')

    submit(browser, form_class='form-configuration')


def bind_get_dnssec(browser):
    """Return whether DNSSEC is enabled/disabled in bind configuration."""
    nav_to_module(browser, 'bind')
    return browser.find_by_name('enable_dnssec').first.checked


def security_enable_restricted_logins(browser, should_enable):
    """Enable/disable restricted logins in security module."""
    nav_to_module(browser, 'security')
    if should_enable:
        browser.check('security-restricted_access')
    else:
        browser.uncheck('security-restricted_access')

    submit(browser)


def security_get_restricted_logins(browser):
    """Return whether restricted console logins is enabled."""
    nav_to_module(browser, 'security')
    return browser.find_by_name('security-restricted_access').first.checked
