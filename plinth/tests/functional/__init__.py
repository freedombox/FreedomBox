# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Utilities for functional testing.
"""

import configparser
import logging
import os
import pathlib
import tempfile
import time
from contextlib import contextmanager

import requests
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait

config = configparser.ConfigParser()
config.read(pathlib.Path(__file__).with_name('config.ini'))

config['DEFAULT']['url'] = os.environ.get('FREEDOMBOX_URL',
                                          config['DEFAULT']['url'])
config['DEFAULT']['samba_port'] = os.environ.get(
    'FREEDOMBOX_SAMBA_PORT', config['DEFAULT']['samba_port'])

logger = logging.getLogger(__name__)

base_url = config['DEFAULT']['url']

_app_checkbox_id = {
    'tor': 'id_tor-enabled',
    'openvpn': 'id_openvpn-enabled',
}

_apps_with_loaders = ['tor']

# unlisted sites just use '/' + site_name as url
_site_url = {
    'wiki': '/ikiwiki',
    'jsxc': '/plinth/apps/jsxc/jsxc/',
    'cockpit': '/_cockpit/',
    'syncthing': '/syncthing/',
}

_sys_modules = [
    'avahi', 'backups', 'bind', 'cockpit', 'config', 'datetime', 'diagnostics',
    'dynamicdns', 'firewall', 'letsencrypt', 'monkeysphere', 'names',
    'networks', 'pagekite', 'performance', 'power', 'security', 'snapshot',
    'ssh', 'storage', 'upgrades', 'users'
]


######################
# Browser Extensions #
######################
def visit(browser, path):
    """Visit a path assuming the base URL as configured."""
    browser.visit(config['DEFAULT']['url'] + path)


def eventually(function, args=[], timeout=30):
    """Execute a function returning a boolean expression till it returns
    True or a timeout is reached"""
    end_time = time.time() + timeout
    current_time = time.time()
    while current_time < end_time:
        if function(*args):
            return True

        time.sleep(0.1)
        current_time = time.time()

    return False


class _PageLoaded():
    """
    Wait until a page (re)loaded.

    - element: Wait until this element gets stale
    - expected_url (optional): Wait for the URL to become <expected_url>.
      This can be necessary to wait for a redirect to finish.
    """

    def __init__(self, element, expected_url=None):
        self.element = element
        self.expected_url = expected_url

    def __call__(self, driver):
        is_stale = False
        try:
            self.element.has_class('whatever_class')
        except StaleElementReferenceException:
            if self.expected_url is None:
                is_stale = True
            else:
                if driver.url.endswith(self.expected_url):
                    is_stale = True
        return is_stale


@contextmanager
def wait_for_page_update(browser, timeout=300, expected_url=None):
    page_body = browser.find_by_tag('body').first
    yield
    WebDriverWait(browser, timeout).until(_PageLoaded(page_body, expected_url))


def _get_site_url(site_name):
    if site_name.startswith('share'):
        site_name = site_name.replace('_', '/')
    url = '/' + site_name
    url = _site_url.get(site_name, url)
    return url


def access_url(browser, site_name):
    browser.visit(config['DEFAULT']['url'] + _get_site_url(site_name))


def is_available(browser, site_name):
    url_to_visit = config['DEFAULT']['url'] + _get_site_url(site_name)
    browser.visit(url_to_visit)
    time.sleep(3)
    browser.reload()
    not_404 = '404' not in browser.title
    # The site might have a default path after the sitename,
    # e.g /mediawiki/Main_Page
    no_redirect = browser.url.startswith(url_to_visit.strip('/'))
    return not_404 and no_redirect


def download_file(browser, url):
    """Return file contents after downloading a URL."""
    cookies = browser.cookies.all()
    response = requests.get(url, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise Exception('URL download failed')

    return response.content


def download_file_outside_browser(url):
    """Download a file to disk given a URL."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        logging.captureWarnings(True)
        request = requests.get(url, verify=False)
        logging.captureWarnings(False)
        temp_file.write(request.content)

    return temp_file.name


###########################
# Form handling utilities #
###########################
def submit(browser, element=None, form_class=None, expected_url=None):
    with wait_for_page_update(browser, expected_url=expected_url):
        if element:
            element.click()
        elif form_class:
            browser.find_by_css(
                '.{} input[type=submit]'.format(form_class)).click()
        else:
            browser.find_by_css('input[type=submit]').click()


def change_checkbox_status(browser, app_name, checkbox_id,
                           change_status_to='enabled'):
    """Change checkbox status."""
    checkbox = browser.find_by_id(checkbox_id)
    if change_status_to == 'enabled':
        checkbox.check()
    else:
        checkbox.uncheck()

    submit(browser, form_class='form-configuration')

    if app_name in _apps_with_loaders:
        wait_for_config_update(browser, app_name)


def wait_for_config_update(browser, app_name):
    while browser.is_element_present_by_css('.running-status.loading'):
        time.sleep(0.1)


############################
# Login handling utilities #
############################
def is_login_prompt(browser):
    return all(
        [browser.find_by_id('id_username'),
         browser.find_by_id('id_password')])


def _create_admin_account(browser, username, password):
    browser.find_by_id('id_username').fill(username)
    browser.find_by_id('id_password1').fill(password)
    browser.find_by_id('id_password2').fill(password)
    submit(browser)


def login(browser, url, username, password):

    # XXX: Find a way to remove the hardcoded jsxc URL
    if '/plinth/' not in browser.url or '/jsxc/jsxc' in browser.url:
        browser.visit(url)

    apps_link = browser.find_link_by_href('/plinth/apps/')
    if len(apps_link):
        return

    login_button = browser.find_link_by_href('/plinth/accounts/login/')
    if login_button:
        login_button.first.click()
        if login_button:
            browser.fill('username', username)
            browser.fill('password', password)
            submit(browser)
    else:
        browser.visit(base_url + '/plinth/firstboot/welcome')
        submit(browser)  # click the "Start Setup" button
        _create_admin_account(browser, username, password)
        if '/network-topology-first-boot' in browser.url:
            submit(browser, element=browser.find_by_name('skip')[0])

        if '/internet-connection-type' in browser.url:
            submit(browser, element=browser.find_by_name('skip')[0])


#################
# App utilities #
#################
def nav_to_module(browser, module):
    sys_or_apps = 'sys' if module in _sys_modules else 'apps'
    required_url = base_url + f'/plinth/{sys_or_apps}/{module}/'
    if browser.url != required_url:
        browser.visit(required_url)


def app_select_domain_name(browser, app_name, domain_name):
    browser.visit('{}/plinth/apps/{}/setup/'.format(base_url, app_name))
    drop_down = browser.find_by_id('id_domain_name')
    drop_down.select(domain_name)
    submit(browser, form_class='form-configuration')


#########################
# App install utilities #
#########################
def _find_install_button(browser, app_name):
    nav_to_module(browser, app_name)
    return browser.find_by_css('.form-install input[type=submit]')


def is_installed(browser, app_name):
    install_button = _find_install_button(browser, app_name)
    return not bool(install_button)


def install(browser, app_name):
    install_button = _find_install_button(browser, app_name)

    def install_in_progress():
        selectors = [
            '.install-state-' + state
            for state in ['pre', 'post', 'installing']
        ]
        return any(
            browser.is_element_present_by_css(selector)
            for selector in selectors)

    def is_server_restarting():
        return browser.is_element_present_by_css('.neterror')

    def wait_for_install():
        if install_in_progress():
            time.sleep(1)
        elif is_server_restarting():
            time.sleep(1)
            browser.visit(browser.url)
        else:
            return
        wait_for_install()

    if install_button:
        install_button.click()
        wait_for_install()
        # sleep(2)  # XXX This shouldn't be required.


################################
# App enable/disable utilities #
################################
def _change_app_status(browser, app_name, change_status_to='enabled'):
    """Enable or disable application."""
    button = browser.find_by_css('button[name="app_enable_disable_button"]')

    if button:
        should_enable_field = browser.find_by_id('id_should_enable')
        if (should_enable_field.value == 'False'
                and change_status_to == 'disabled') or (
                    should_enable_field.value == 'True'
                    and change_status_to == 'enabled'):
            submit(browser, element=button)
    else:
        checkbox_id = _app_checkbox_id[app_name]
        change_checkbox_status(browser, app_name, checkbox_id,
                               change_status_to)

    if app_name in _apps_with_loaders:
        wait_for_config_update(browser, app_name)


def app_enable(browser, app_name):
    nav_to_module(browser, app_name)
    _change_app_status(browser, app_name, 'enabled')


def app_disable(browser, app_name):
    nav_to_module(browser, app_name)
    _change_app_status(browser, app_name, 'disabled')


def app_can_be_disabled(browser, app_name):
    """Return whether the application can be disabled."""
    nav_to_module(browser, app_name)
    button = browser.find_by_css('button[name="app_enable_disable_button"]')
    return bool(button)


#########################
# Domain name utilities #
#########################
def set_domain_name(browser, domain_name):
    nav_to_module(browser, 'config')
    browser.find_by_id('id_domainname').fill(domain_name)
    submit(browser)
    # After a domain name change, Let's Encrypt will reload the web server and
    # could cause a connection failure.
    if browser.find_by_id('netErrorButtonContainer'):
        browser.visit(browser.url)


########################
# Front page utilities #
########################
def find_on_front_page(browser, app_name):
    browser.visit(base_url)
    shortcuts = browser.find_link_by_href(f'/{app_name}/')
    return shortcuts


####################
# Daemon utilities #
####################
def service_is_running(browser, app_name):
    nav_to_module(browser, app_name)
    return len(browser.find_by_id('service-not-running')) == 0


def service_is_not_running(browser, app_name):
    nav_to_module(browser, app_name)
    return len(browser.find_by_id('service-not-running')) != 0


##############################
# System -> Config utilities #
##############################
def set_advanced_mode(browser, mode):
    nav_to_module(browser, 'config')
    advanced_mode = browser.find_by_id('id_advanced_mode')
    if mode:
        advanced_mode.check()
    else:
        advanced_mode.uncheck()

    submit(browser)


####################
# Backup utilities #
####################
def _click_button_and_confirm(browser, href):
    buttons = browser.find_link_by_href(href)
    if buttons:
        buttons.first.click()
        with wait_for_page_update(browser,
                                  expected_url='/plinth/sys/backups/'):
            submit(browser)


def _backup_delete_archive_by_name(browser, archive_name):
    nav_to_module(browser, 'backups')
    href = f'/plinth/sys/backups/root/delete/{archive_name}/'
    _click_button_and_confirm(browser, href)


def backup_create(browser, app_name, archive_name=None):
    install(browser, 'backups')
    if archive_name:
        _backup_delete_archive_by_name(browser, archive_name)

    browser.find_link_by_href('/plinth/sys/backups/create/').first.click()
    browser.find_by_id('select-all').uncheck()
    if archive_name:
        browser.find_by_id('id_backups-name').fill(archive_name)

    # ensure the checkbox is scrolled into view
    browser.execute_script('window.scrollTo(0, 0)')
    browser.find_by_value(app_name).first.check()
    submit(browser)


def backup_restore(browser, app_name, archive_name=None):
    nav_to_module(browser, 'backups')
    href = f'/plinth/sys/backups/root/restore-archive/{archive_name}/'
    _click_button_and_confirm(browser, href)


######################
# Networks utilities #
######################
def networks_set_firewall_zone(browser, zone):
    """"Set the network device firewall zone as internal or external."""
    nav_to_module(browser, 'networks')
    device = browser.find_by_xpath(
        '//span[contains(@class, "label-success") '
        'and contains(@class, "connection-status-label")]/following::a').first
    network_id = device['href'].split('/')[-3]
    device.click()
    edit_url = "/plinth/sys/networks/{}/edit/".format(network_id)
    browser.find_link_by_href(edit_url).first.click()
    browser.select('zone', zone)
    browser.find_by_tag("form").first.find_by_tag('input')[-1].click()


##################
# Bind utilities #
##################
def set_forwarders(browser, forwarders):
    """Set the forwarders list (space separated) in bind configuration."""
    nav_to_module(browser, 'bind')
    browser.fill('forwarders', forwarders)
    submit(browser, form_class='form-configuration')


def get_forwarders(browser):
    """Return the forwarders list (space separated) in bind configuration."""
    nav_to_module(browser, 'bind')
    return browser.find_by_name('forwarders').first.value
