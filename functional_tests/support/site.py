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

from time import sleep

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from support import config, interface
from support.service import eventually, wait_for_page_update

# unlisted sites just use '/' + site_name as url
site_url = {
    'wiki': '/ikiwiki',
    'jsxc': '/plinth/apps/jsxc/jsxc/',
    'cockpit': '/_cockpit/'
}


def get_site_url(site_name):
    url = '/' + site_name
    if site_name in site_url:
        url = site_url[site_name]
    return url


def is_available(browser, site_name):
    browser.visit(config['DEFAULT']['url'] + get_site_url(site_name))
    sleep(3)
    browser.reload()
    return '404' not in browser.title


def access_url(browser, site_name):
    browser.visit(config['DEFAULT']['url'] + get_site_url(site_name))


def verify_coquelicot_upload_password(browser, password):
    browser.visit(config['DEFAULT']['url'] + '/coquelicot')
    browser.find_by_id('upload_password').fill(password)
    actions = ActionChains(browser.driver)
    actions.send_keys(Keys.RETURN)
    actions.perform()
    assert eventually(browser.is_element_present_by_css,
                      args=['div[style*="display: none;"]'])


def verify_mediawiki_create_account_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_present_by_id,
                      args=['pt-createaccount'])


def verify_mediawiki_no_create_account_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_not_present_by_id,
                      args=['pt-createaccount'])


def verify_mediawiki_anonymous_reads_edits_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_present_by_id, args=['ca-nstab-main'])


def verify_mediawiki_no_anonymous_reads_edits_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_not_present_by_id,
                      args=['ca-nstab-main'])
    assert eventually(browser.is_element_present_by_id,
                      args=['ca-nstab-special'])


def login_to_mediawiki_with_credentials(browser, username, password):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    browser.find_by_id('pt-login').click()
    browser.find_by_id('wpName1').fill(username)
    browser.find_by_id('wpPassword1').fill(password)
    with wait_for_page_update(browser):
        browser.find_by_id('wpLoginAttempt').click()
    # Had to put it in the same step because sessions don't
    # persist between steps
    assert eventually(browser.is_element_present_by_id, args=['t-upload'])
