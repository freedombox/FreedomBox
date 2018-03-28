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

from .service import wait_for_page_update

sys_modules = [
    'avahi', 'cockpit', 'config', 'datetime', 'diagnostics', 'firewall',
    'letsencrypt', 'monkeysphere', 'names', 'networks', 'power', 'snapshot',
    'upgrades', 'users'
]

default_url = config['DEFAULT']['url']


def login(browser, url, username, password):
    browser.visit(url)

    # XXX browser.visit goes to the web page with no cookies,
    # hence there should be some kind of session storage for this to work

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
        login(browser, url, username, password)


def is_login_prompt(browser):
    return all(
        [browser.find_by_id('id_username'),
         browser.find_by_id('id_password')])


def nav_to_module(browser, module):
    with wait_for_page_update(browser):
        browser.find_link_by_href('/plinth/').first.click()
    if module in sys_modules:
        with wait_for_page_update(browser):
            browser.find_link_by_href('/plinth/sys/').first.click()
        with wait_for_page_update(browser):
            browser.find_link_by_href(
                '/plinth/sys/' + module + '/').first.click()
    else:
        with wait_for_page_update(browser):
            browser.find_link_by_href('/plinth/apps/').first.click()
        with wait_for_page_update(browser):
            browser.find_link_by_href(
                '/plinth/apps/' + module + '/').first.click()


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
        browser.find_link_by_href(
            '/plinth/sys/users/' + old_name + '/edit/').first.click()
    browser.find_by_id('id_username').fill(new_name)
    submit(browser)


def delete_user(browser, name):
    nav_to_module(browser, 'users')
    with wait_for_page_update(browser):
        delete_link = browser.find_link_by_href(
            '/plinth/sys/users/' + name + '/delete/')
        if delete_link:
            delete_link.first.click()
    if delete_link:
        submit(browser)


def is_user(browser, name):
    nav_to_module(browser, 'users')
    return browser.is_text_present(name)


def create_admin_account(browser, username, password):
    browser.find_by_id('id_username').fill(username)
    browser.find_by_id('id_password1').fill(password)
    browser.find_by_id('id_password2').fill(password)
    submit(browser)


def submit(browser, form_class=None):
    with wait_for_page_update(browser):
        if form_class:
            browser.find_by_css(
                '.{} input[type=submit]'.format(form_class)).click()
        else:
            browser.find_by_css('input[type=submit]').click()
