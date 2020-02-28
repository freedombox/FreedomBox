# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import random
import tempfile

import requests

from support import config

from .service import wait_for_page_update

sys_modules = [
    'avahi', 'backups', 'bind', 'cockpit', 'config', 'datetime', 'diagnostics',
    'dynamicdns', 'firewall', 'letsencrypt', 'monkeysphere', 'names',
    'networks', 'pagekite', 'performance', 'power', 'security', 'snapshot',
    'ssh', 'storage', 'upgrades', 'users'
]

default_url = config['DEFAULT']['url']


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
        browser.visit(default_url + '/plinth/firstboot/welcome')
        submit(browser)  # click the "Start Setup" button
        create_admin_account(browser, username, password)
        if '/network-topology-first-boot' in browser.url:
            submit(browser, element=browser.find_by_name('skip')[0])

        if '/internet-connection-type' in browser.url:
            submit(browser, element=browser.find_by_name('skip')[0])


def is_login_prompt(browser):
    return all(
        [browser.find_by_id('id_username'),
         browser.find_by_id('id_password')])


def nav_to_module(browser, module):
    sys_or_apps = 'sys' if module in sys_modules else 'apps'
    required_url = default_url + f'/plinth/{sys_or_apps}/{module}/'
    if browser.url != required_url:
        browser.visit(required_url)


def create_user(browser, name, password):
    nav_to_module(browser, 'users')
    with wait_for_page_update(browser):
        browser.find_link_by_href('/plinth/sys/users/create/').first.click()
    browser.find_by_id('id_username').fill(name)
    browser.find_by_id('id_password1').fill(password)
    browser.find_by_id('id_password2').fill(password)
    submit(browser)


def rename_user(browser, old_name, new_name):
    nav_to_module(browser, 'users')
    with wait_for_page_update(browser):
        browser.find_link_by_href('/plinth/sys/users/' + old_name +
                                  '/edit/').first.click()
    browser.find_by_id('id_username').fill(new_name)
    submit(browser)


def delete_user(browser, name):
    nav_to_module(browser, 'users')
    delete_link = browser.find_link_by_href('/plinth/sys/users/' + name +
                                            '/delete/')
    if delete_link:
        with wait_for_page_update(browser):
            delete_link.first.click()
        submit(browser)


def is_user(browser, name):
    nav_to_module(browser, 'users')
    edit_link = browser.find_link_by_href('/plinth/sys/users/' + name +
                                          '/edit/')
    return bool(edit_link)


def create_admin_account(browser, username, password):
    browser.find_by_id('id_username').fill(username)
    browser.find_by_id('id_password1').fill(password)
    browser.find_by_id('id_password2').fill(password)
    submit(browser)


def submit(browser, element=None, form_class=None, expected_url=None):
    with wait_for_page_update(browser, expected_url=expected_url):
        if element:
            element.click()
        elif form_class:
            browser.find_by_css(
                '.{} input[type=submit]'.format(form_class)).click()
        else:
            browser.find_by_css('input[type=submit]').click()


def create_sample_local_file():
    """Create a sample file for upload using browser."""
    contents = bytearray(random.getrandbits(8) for _ in range(64))
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(contents)

    return temp_file.name, contents


def download_file(url):
    """Download a file to disk given a URL."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        logging.captureWarnings(True)
        request = requests.get(url, verify=False)
        logging.captureWarnings(False)
        temp_file.write(request.content)

    return temp_file.name


def compare_files(file1, file2):
    """Assert that the contents of two files are the same."""
    file1_contents = open(file1, 'rb').read()
    file2_contents = open(file2, 'rb').read()

    assert file1_contents == file2_contents


def go_to_status_logs(browser):
    browser.visit(default_url + '/plinth/help/status-log/')


def are_status_logs_shown(browser):
    return browser.is_text_present('Logs begin')
