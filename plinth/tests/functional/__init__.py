# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Utilities for functional testing.
"""

import configparser
import logging
import os
import pathlib
import subprocess
import tempfile
import time
import warnings
from contextlib import contextmanager

import pytest
import requests
from selenium.common.exceptions import (StaleElementReferenceException,
                                        WebDriverException)
from selenium.webdriver.support.ui import WebDriverWait

config = configparser.ConfigParser()
config.read(pathlib.Path(__file__).with_name('config.ini'))

config['DEFAULT']['url'] = os.environ.get('FREEDOMBOX_URL',
                                          config['DEFAULT']['url']).rstrip('/')
config['DEFAULT']['ssh_port'] = os.environ.get('FREEDOMBOX_SSH_PORT',
                                               config['DEFAULT']['ssh_port'])
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
    'dynamicdns', 'firewall', 'letsencrypt', 'names', 'networks', 'pagekite',
    'performance', 'power', 'security', 'snapshot', 'ssh', 'storage',
    'upgrades', 'users'
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
        try:
            if function(*args):
                return True
        except Exception:
            pass

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
            # After a domain name change, Let's Encrypt will restart the web
            # server and could cause a connection failure.
            if driver.find_by_id('netErrorButtonContainer'):
                try:
                    driver.visit(driver.url)
                except WebDriverException:
                    pass
                return False

            is_fully_loaded = driver.execute_script(
                'return document.readyState;') == 'complete'
            if not is_fully_loaded:
                is_stale = False
            elif self.expected_url is None:
                is_stale = True
            else:
                if driver.url.endswith(self.expected_url):
                    is_stale = True

        return is_stale


@contextmanager
def wait_for_page_update(browser, timeout=300, expected_url=None):
    page_body = browser.find_by_tag('body').first
    try:
        yield
    except WebDriverException:
        # ignore a connection failure which may happen after web server restart
        pass

    WebDriverWait(browser, timeout).until(_PageLoaded(page_body, expected_url))


def _get_site_url(site_name):
    if site_name.startswith('share'):
        site_name = site_name.replace('_', '/')
    url = '/' + site_name
    url = _site_url.get(site_name, url)
    return url


def access_url(browser, site_name):
    browser.visit(config['DEFAULT']['url'] + _get_site_url(site_name))


def get_password(username):
    """Get a user password."""
    if username == config['DEFAULT']['username']:
        return config['DEFAULT']['password']
    return 'password@&123_{}'.format(username)


def is_available(browser, site_name):
    url_to_visit = config['DEFAULT']['url'] + _get_site_url(site_name)
    browser.visit(url_to_visit)
    time.sleep(3)
    browser.reload()
    not_404 = '404' not in browser.title
    # The site might have a default path after the sitename,
    # e.g /mediawiki/Main_Page
    print('URL =', browser.url, url_to_visit, browser.title)
    browser_url = browser.url.partition('://')[2]
    url_to_visit_without_proto = url_to_visit.strip('/').partition('://')[2]
    no_redirect = browser_url.startswith(url_to_visit_without_proto)
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
    """Wait until the configuration update progress goes away.

    Perform an atomic check that page is fully loaded and that progress icon is
    not present at the same time to avoid race conditions due to automatic page
    reloads.

    """
    script = 'return (document.readyState == "complete") && ' \
        '(!Boolean(document.querySelector(".running-status.loading")));'
    while not browser.execute_script(script):
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


def login(browser):
    """Login to the FreedomBox interface with default test account."""
    login_with_account(browser, base_url, config['DEFAULT']['username'],
                       config['DEFAULT']['password'])


def login_with_account(browser, url, username, password=None):
    """Login to the FreedomBox interface with provided account."""
    if password is None:
        password = get_password(username)
    # XXX: Find a way to remove the hardcoded jsxc URL
    if '/plinth/' not in browser.url or '/jsxc/jsxc' in browser.url:
        browser.visit(url)

    user_menu = browser.find_by_id('id_user_menu')

    if len(user_menu):
        if user_menu.text == username:
            return

        visit(browser, '/plinth/accounts/logout/')

    login_button = browser.links.find_by_href('/plinth/accounts/login/')
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

        if '/firstboot/backports' in browser.url:
            submit(browser, element=browser.find_by_name('next')[0])

        if '/firstboot/update' in browser.url:
            browser.find_by_id('id_update_now').uncheck()
            submit(browser, element=browser.find_by_name('next')[0])


def logout(browser):
    """Log out of the FreedomBox interface."""
    visit(browser, '/plinth/accounts/logout/')


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
def is_installed(browser, app_name):
    nav_to_module(browser, app_name)
    return not bool(browser.find_by_css('.form-install input[type=submit]'))


def install(browser, app_name):
    nav_to_module(browser, app_name)
    install_button_css = '.form-install input[type=submit]'
    while True:
        script = 'return (document.readyState == "complete") && ' \
            '(!Boolean(document.querySelector(".installing")));'
        if not browser.execute_script(script):
            time.sleep(0.1)
        elif browser.is_element_present_by_css('.neterror'):
            browser.visit(browser.url)
        elif browser.is_element_present_by_css('.alert-danger'):
            break
        elif browser.is_element_present_by_css(install_button_css):
            install_button = browser.find_by_css(install_button_css).first
            if install_button['disabled']:
                if not browser.find_by_name('refresh-packages'):
                    # Package manager is busy, wait and refresh page
                    time.sleep(1)
                    browser.visit(browser.url)
                else:
                    # This app is not available in this distribution
                    warnings.warn(
                        f'App {app_name} is not available in distribution')
                    pytest.skip('App not available in distribution')
            else:
                install_button.click()
        else:
            break


################################
# App enable/disable utilities #
################################
def _change_app_status(browser, app_name, change_status_to='enabled'):
    """Enable or disable application."""
    button = browser.find_by_css('button[name="app_enable_disable_button"]')

    if button:
        should_enable_field = browser.find_by_id('id_should_enable')
        if (should_enable_field.value == 'False' and change_status_to
                == 'disabled') or (should_enable_field.value == 'True'
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


def app_is_enabled(browser, app_name):
    """Return whether the app is enabled."""
    nav_to_module(browser, app_name)
    should_enable_field = browser.find_by_id('id_should_enable')
    return should_enable_field.value == 'False'


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
    update_setup = browser.find_by_css('.btn-primary[type="submit"]')
    submit(browser, element=update_setup)


########################
# Front page utilities #
########################
def find_on_front_page(browser, app_name):
    browser.visit(base_url)
    shortcuts = browser.links.find_by_href(f'/{app_name}/')
    return shortcuts


def is_visible_on_front_page(browser, app_name):
    shortcuts = find_on_front_page(browser, app_name)
    return len(shortcuts) == 1


####################
# Daemon utilities #
####################
def service_is_running(browser, app_name):
    nav_to_module(browser, app_name)
    return len(browser.find_by_id('service-not-running')) == 0


def service_is_not_running(browser, app_name):
    nav_to_module(browser, app_name)
    return len(browser.find_by_id('service-not-running')) != 0


def running_inside_container():
    """Check if freedombox is running inside a container"""
    # If the URL to connect to was overridden then assume that we are running
    # tests on a different machine than the machine running freedombox. Assume
    # running inside container to be conservative about tests.
    if config['DEFAULT']['url'] != 'https://localhost':
        return True

    # If URL is not overridden then testing code and freedombox are running on
    # the same machine. Proceed with a proper test.
    result = subprocess.run(['systemd-detect-virt', '--container'],
                            stdout=subprocess.PIPE, check=False)
    return result.stdout.decode('utf-8').strip().lower() != 'none'


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

    update_setup = browser.find_by_css('.btn-primary')
    submit(browser, element=update_setup)


####################
# Backup utilities #
####################
def _click_button_and_confirm(browser, href):
    buttons = browser.links.find_by_href(href)
    if buttons:
        submit(browser, buttons.first)
        submit(browser, expected_url='/plinth/sys/backups/')


def _backup_delete_archive_by_name(browser, archive_name):
    nav_to_module(browser, 'backups')
    href = f'/plinth/sys/backups/root/delete/{archive_name}/'
    _click_button_and_confirm(browser, href)


def backup_create(browser, app_name, archive_name=None):
    install(browser, 'backups')
    if archive_name:
        _backup_delete_archive_by_name(browser, archive_name)

    buttons = browser.links.find_by_href('/plinth/sys/backups/create/')
    submit(browser, buttons.first)
    eventually(browser.find_by_css, args=['.select-all'])
    browser.find_by_css('.select-all').first.uncheck()
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
        '//span[contains(@class, "badge-success") '
        'and contains(@class, "connection-status-label")]/following::a').first
    network_id = device['href'].split('/')[-3]
    device.click()
    edit_url = "/plinth/sys/networks/{}/edit/".format(network_id)
    browser.links.find_by_href(edit_url).first.click()
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


##############################
# Users and Groups utilities #
##############################


def create_user(browser, name, password=None, groups=[]):
    """Create a user with password and user groups."""
    nav_to_module(browser, 'users')

    if password is None:
        password = get_password(name)

    with wait_for_page_update(browser):
        browser.links.find_by_href('/plinth/sys/users/create/').first.click()

    browser.find_by_id('id_username').fill(name)
    browser.find_by_id('id_password1').fill(password)
    browser.find_by_id('id_password2').fill(password)

    for group in groups:
        browser.find_by_id(f'id_groups_{group}').check()

    browser.find_by_id('id_confirm_password').fill(
        config['DEFAULT']['password'])

    submit(browser)


def delete_user(browser, name):
    """Delete a user."""
    nav_to_module(browser, 'users')
    delete_link = browser.links.find_by_href(
        f'/plinth/sys/users/{name}/delete/')

    with wait_for_page_update(browser):
        delete_link.first.click()
    submit(browser)


def user_exists(browser, name):
    """Check if a user with a given name exists."""
    nav_to_module(browser, 'users')
    links = browser.links.find_by_href(f'/plinth/sys/users/{name}/edit/')
    return len(links) == 1


class BaseAppTests:
    """Base class for common functional tests.

    To run these tests on an app, the app should subclass this class with a
    class name starting with 'Test'. This allows the app tests to be
    automatically discovered while the base class tests to stay undiscovered.
    Tests will apply to the app without the need not override each test.
    """

    app_name = ''
    # TODO: Check the components of the app instead of configuring here.
    has_service = False
    has_web = True
    check_diagnostics = True
    diagnostics_delay = 0

    def assert_app_running(self, session_browser):
        """Assert that the app is running."""
        if self.has_service:
            assert service_is_running(session_browser, self.app_name)

        if self.has_web:
            assert is_available(session_browser, self.app_name)

    def assert_app_not_running(self, session_browser):
        """Assert that the app is not running."""
        if self.has_service:
            assert service_is_not_running(session_browser, self.app_name)

        if self.has_web:
            assert not is_available(session_browser, self.app_name)

    @pytest.fixture(autouse=True)
    def fixture_background(self, session_browser):
        """Login, install, and enable the app."""
        login(session_browser)
        install(session_browser, self.app_name)
        app_enable(session_browser, self.app_name)
        yield
        login(session_browser)
        app_disable(session_browser, self.app_name)

    def test_enable_disable(self, session_browser):
        """Test enabling and disabling the app."""
        app_disable(session_browser, self.app_name)
        self.assert_app_not_running(session_browser)

        app_enable(session_browser, self.app_name)
        self.assert_app_running(session_browser)

    def test_run_diagnostics(self, session_browser):
        """Test that all app diagnostics are passing."""
        if not self.check_diagnostics:
            pytest.skip(f'Skipping diagnostics check for {self.app_name}.')

        time.sleep(self.diagnostics_delay)
        session_browser.find_by_id('id_extra_actions_button').click()
        submit(session_browser, form_class='form-diagnostics-button')

        warning_results = session_browser.find_by_css('.badge-warning')
        if warning_results:
            warnings.warn(
                f'Diagnostics warnings for {self.app_name}: {warning_results}')

        failure_results = session_browser.find_by_css('.badge-danger')
        assert not failure_results

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test that backup and restore operations work on the app."""
        backup_create(session_browser, self.app_name, 'test_' + self.app_name)
        backup_restore(session_browser, self.app_name, 'test_' + self.app_name)
        self.assert_app_running(session_browser)
