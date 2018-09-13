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


def _login_to_mediawiki(browser, username, password):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    browser.find_by_id('pt-login').click()
    browser.find_by_id('wpName1').fill(username)
    browser.find_by_id('wpPassword1').fill(password)
    with wait_for_page_update(browser):
        browser.find_by_id('wpLoginAttempt').click()


def login_to_mediawiki_with_credentials(browser, username, password):
    _login_to_mediawiki(browser, username, password)
    # Had to put it in the same step because sessions don't
    # persist between steps
    assert eventually(browser.is_element_present_by_id, args=['t-upload'])


def upload_image_mediawiki(browser, username, password, image):
    """Upload an image to MediaWiki. Idempotent."""
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    _login_to_mediawiki(browser, username, password)

    # Upload file
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:Upload')
    file_path = os.path.realpath(
        '../static/themes/default/img/' + image)
    browser.attach_file('wpUploadFile', file_path)
    interface.submit(browser, element=browser.find_by_name('wpUpload')[0])


def get_number_of_uploaded_images_in_mediawiki(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:ListFiles')
    return len(browser.find_by_css('.TablePager_col_img_timestamp'))


def get_uploaded_image_in_mediawiki(browser, image):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:ListFiles')
    elements = browser.find_link_by_partial_href(image)
    return elements[0].value


def mediawiki_delete_main_page(browser):
    """Delete the mediawiki main page."""
    _login_to_mediawiki(browser, 'admin', 'whatever123')
    browser.visit(
        '{}/mediawiki/index.php?title=Main_Page&action=delete'.format(
            interface.default_url))
    with wait_for_page_update(browser):
        browser.find_by_id('wpConfirmB').first.click()


def mediawiki_has_main_page(browser):
    """Check if mediawiki main page exists."""
    browser.visit('{}/mediawiki/Main_Page'.format(interface.default_url))
    content = browser.find_by_id('mw-content-text').first
    return 'This page has been deleted.' not in content.text


def repro_configure(browser):
    """Configure repro."""
    browser.visit(
        '{}/repro/domains.html?domainUri=freedombox.local&domainTlsPort='
        '&action=Add'.format(interface.default_url))


def repro_delete_config(browser):
    """Delete the repro config."""
    browser.visit('{}/repro/domains.html?domainUri=&domainTlsPort='
                  '&action=Remove&remove.freedombox.local=on'.format(
                      interface.default_url))


def repro_is_configured(browser):
    """Check whether repro is configured."""
    browser.visit('{}/repro/domains.html'.format(interface.default_url))
    remove = browser.find_by_name('remove.freedombox.local')
    return bool(remove)
