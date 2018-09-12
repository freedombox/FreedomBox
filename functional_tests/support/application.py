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

import splinter

from support import config, interface
from support.interface import submit
from support.service import eventually, wait_for_page_update

# unlisted apps just use the app_name as module name
app_module = {
    'ntp': 'datetime',
    'wiki': 'ikiwiki',
    'tt-rss': 'ttrss',
}

app_checkbox_id = {
    'tor': 'id_tor-enabled',
}

default_url = config['DEFAULT']['url']

apps_with_loaders = ['tor']


def get_app_module(app_name):
    module = app_name
    if app_name in app_module:
        module = app_module[app_name]
    return module


def get_app_checkbox_id(app_name):
    checkbox_id = 'id_is_enabled'
    if app_name in app_checkbox_id:
        checkbox_id = app_checkbox_id[app_name]
    return checkbox_id


def install(browser, app_name):
    interface.nav_to_module(browser, get_app_module(app_name))
    install = browser.find_by_css('.form-install input[type=submit]')

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
            sleep(1)
        elif is_server_restarting():
            sleep(1)
            browser.visit(browser.url)
        else:
            return
        wait_for_install()

    if install:
        install.click()
        wait_for_install()
        sleep(2)  # XXX This shouldn't be required.


def _change_status(browser, app_name, change_status_to='enabled',
                   checkbox_id=None):
    interface.nav_to_module(browser, get_app_module(app_name))
    checkbox_id = checkbox_id or get_app_checkbox_id(app_name)
    checkbox = browser.find_by_id(checkbox_id)
    checkbox.check() if change_status_to == 'enabled' else checkbox.uncheck()
    interface.submit(browser, form_class='form-configuration')
    if app_name in apps_with_loaders:
        wait_for_config_update(browser, app_name)


def enable(browser, app_name):
    _change_status(browser, app_name, 'enabled')


def disable(browser, app_name):
    _change_status(browser, app_name, 'disabled')


def wait_for_config_update(browser, app_name):
    while browser.is_element_present_by_css('.running-status.loading'):
        sleep(0.1)


def select_domain_name(browser, app_name, domain_name):
    browser.visit('{}/plinth/apps/{}/setup/'.format(default_url, app_name))
    drop_down = browser.find_by_id('id_domain_name')
    drop_down.select(domain_name)
    interface.submit(browser, form_class='form-configuration')


def configure_shadowsocks(browser):
    """Configure shadowsocks client with some fake server details"""
    browser.visit('{}/plinth/apps/shadowsocks/'.format(default_url))
    browser.find_by_id('id_server').fill('some.shadow.tunnel')
    browser.find_by_id('id_password').fill('fakepassword')
    interface.submit(browser, form_class='form-configuration')


def modify_max_file_size(browser, size):
    """Change the maximum file size of coquelicot to the given value"""
    browser.visit('{}/plinth/apps/coquelicot/'.format(default_url))
    browser.find_by_id('id_max_file_size').fill(size)
    interface.submit(browser, form_class='form-configuration')


def get_max_file_size(browser):
    """Get the maximum file size of coquelicot"""
    browser.visit('{}/plinth/apps/coquelicot/'.format(default_url))
    return int(browser.find_by_id('id_max_file_size').value)


def modify_upload_password(browser, password):
    """Change the upload password for coquelicot to the given value"""
    browser.visit('{}/plinth/apps/coquelicot/'.format(default_url))
    browser.find_by_id('id_upload_password').fill(password)
    interface.submit(browser, form_class='form-configuration')


# Sharing app helper functions


def remove_share(browser, name):
    """Remove a share in sharing app."""
    try:
        share_row = get_share(browser, name)
    except splinter.exceptions.ElementDoesNotExist:
        pass
    else:
        share_row.find_by_css('.share-remove')[0].click()


def add_share(browser, name, path, group):
    """Add a share in sharing app."""
    browser.visit('{}/plinth/apps/sharing/add/'.format(default_url))
    browser.fill('sharing-name', name)
    browser.fill('sharing-path', path)
    browser.find_by_css(
        '#id_sharing-groups input[value="{}"]'.format(group)).check()
    submit(browser)


def edit_share(browser, old_name, new_name, path, group):
    """Edit a share in sharing app."""
    row = get_share(browser, old_name)
    with wait_for_page_update(browser):
        row.find_by_css('.share-edit')[0].click()
    browser.fill('sharing-name', new_name)
    browser.fill('sharing-path', path)
    browser.find_by_css('#id_sharing-groups input').uncheck()
    browser.find_by_css(
        '#id_sharing-groups input[value="{}"]'.format(group)).check()
    submit(browser)


def get_share(browser, name):
    """Return the row for a given share."""
    browser.visit('{}/plinth/apps/sharing/'.format(default_url))
    return browser.find_by_id('share-{}'.format(name))[0]


def verify_share(browser, name, path, group):
    """Verfiy that a share exists in list of shares."""
    href = '{}/share/{}'.format(default_url, name)
    url = '/share/{}'.format(name)
    row = get_share(browser, name)
    assert row.find_by_css('.share-name')[0].text == name
    assert row.find_by_css('.share-path')[0].text == path
    assert row.find_by_css('.share-url a')[0]['href'] == href
    assert row.find_by_css('.share-url a')[0].text == url
    assert row.find_by_css('.share-groups')[0].text == group


def access_share(browser, name):
    """Visit a share and see if it is accessible."""
    row = get_share(browser, name)
    url = row.find_by_css('.share-url a')[0]['href']
    browser.visit(url)
    assert '/share/{}'.format(name) in browser.title


def verify_nonexistant_share(browser, name):
    """Verify that given URL for a given share name is a 404."""
    url = '{}/share/{}'.format(default_url, name)
    browser.visit(url)
    assert '404' in browser.title


def verify_inaccessible_share(browser, name):
    """Verify that given URL for a given share name denies permission."""
    url = '{}/share/{}'.format(default_url, name)
    browser.visit(url)
    eventually(lambda: '/plinth' in browser.url, args=[])


def enable_mediawiki_public_registrations(browser):
    """Enable public registrations in MediaWiki."""
    interface.nav_to_module(browser, 'mediawiki')
    _change_status(browser, 'mediawiki', 'enabled',
                   checkbox_id='id_enable_public_registrations')


def disable_mediawiki_public_registrations(browser):
    """Enable public registrations in MediaWiki."""
    interface.nav_to_module(browser, 'mediawiki')
    _change_status(browser, 'mediawiki', 'disabled',
                   checkbox_id='id_enable_public_registrations')


def enable_mediawiki_private_mode(browser):
    """Enable public registrations in MediaWiki."""
    interface.nav_to_module(browser, 'mediawiki')
    _change_status(browser, 'mediawiki', 'enabled',
                   checkbox_id='id_enable_private_mode')


def disable_mediawiki_private_mode(browser):
    """Enable public registrations in MediaWiki."""
    interface.nav_to_module(browser, 'mediawiki')
    _change_status(browser, 'mediawiki', 'disabled',
                   checkbox_id='id_enable_private_mode')


def set_mediawiki_admin_password(browser, password):
    """Set a password for the MediaWiki user called admin."""
    interface.nav_to_module(browser, 'mediawiki')
    browser.find_by_id('id_password').fill(password)
    interface.submit(browser, form_class='form-configuration')


def enable_ejabberd_message_archive_management(browser):
    """Enable Message Archive Management in Ejabberd."""
    interface.nav_to_module(browser, 'ejabberd')
    _change_status(browser, 'ejabberd', 'enabled',
                   checkbox_id='id_MAM_enabled')


def disable_ejabberd_message_archive_management(browser):
    """Enable Message Archive Management in Ejabberd."""
    interface.nav_to_module(browser, 'ejabberd')
    _change_status(browser, 'ejabberd', 'disabled',
                   checkbox_id='id_MAM_enabled')


def ikiwiki_create_wiki_if_needed(browser):
    """Create wiki if it does not exist."""
    interface.nav_to_module(browser, 'ikiwiki')
    browser.find_link_by_href('/plinth/apps/ikiwiki/manage/').first.click()
    wiki = browser.find_link_by_href('/ikiwiki/wiki')
    if not wiki:
        browser.find_link_by_href('/plinth/apps/ikiwiki/create/').first.click()
        browser.find_by_id('id_ikiwiki-name').fill('wiki')
        browser.find_by_id('id_ikiwiki-admin_name').fill(
            config['DEFAULT']['username'])
        browser.find_by_id('id_ikiwiki-admin_password').fill(
            config['DEFAULT']['password'])
        submit(browser)


def ikiwiki_delete_wiki(browser):
    """Delete wiki."""
    interface.nav_to_module(browser, 'ikiwiki')
    browser.find_link_by_href('/plinth/apps/ikiwiki/manage/').first.click()
    browser.find_link_by_href(
        '/plinth/apps/ikiwiki/wiki/delete/').first.click()
    submit(browser)


def ikiwiki_wiki_exists(browser):
    """Check whether the wiki exists."""
    interface.nav_to_module(browser, 'ikiwiki')
    browser.find_link_by_href('/plinth/apps/ikiwiki/manage/').first.click()
    wiki = browser.find_link_by_href('/ikiwiki/wiki')
    return bool(wiki)
