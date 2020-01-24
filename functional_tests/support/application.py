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

import contextlib
import os
import random
import shutil
import string
import subprocess
import tempfile
import urllib
from time import sleep

import requests
import splinter

from support import config, interface, site
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
    'openvpn': 'id_openvpn-enabled',
}

default_url = config['DEFAULT']['url']

apps_with_loaders = ['tor']


def get_app_module(app_name):
    module = app_name
    if app_name in app_module:
        module = app_module[app_name]
    return module


def get_app_checkbox_id(app_name):
    checkbox_id = 'app-toggle-input'
    if app_name in app_checkbox_id:
        checkbox_id = app_checkbox_id[app_name]
    return checkbox_id


def _find_install_button(browser, app_name):
    interface.nav_to_module(browser, get_app_module(app_name))
    return browser.find_by_css('.form-install input[type=submit]')


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
            sleep(1)
        elif is_server_restarting():
            sleep(1)
            browser.visit(browser.url)
        else:
            return
        wait_for_install()

    if install_button:
        install_button.click()
        wait_for_install()
        # sleep(2)  # XXX This shouldn't be required.


def is_installed(browser, app_name):
    install_button = _find_install_button(browser, app_name)
    return not bool(install_button)


def _change_app_status(browser, app_name, change_status_to='enabled'):
    """Enable or disable application."""
    button = browser.find_by_id('app-toggle-button')
    checkbox_id = get_app_checkbox_id(app_name)
    checkbox = browser.find_by_id(checkbox_id)
    if button:
        if checkbox.checked and change_status_to == 'disabled' or (
                not checkbox.checked and change_status_to == 'enabled'):
            interface.submit(browser, element=button)
    else:
        _change_status(browser, app_name, checkbox_id, change_status_to)

    if app_name in apps_with_loaders:
        wait_for_config_update(browser, app_name)


def _change_status(browser, app_name, checkbox_id, change_status_to='enabled'):
    """Change checkbox status."""
    checkbox = browser.find_by_id(checkbox_id)
    checkbox.check() if change_status_to == 'enabled' else checkbox.uncheck()
    interface.submit(browser, form_class='form-configuration')

    if app_name in apps_with_loaders:
        wait_for_config_update(browser, app_name)


def enable(browser, app_name):
    interface.nav_to_module(browser, get_app_module(app_name))
    _change_app_status(browser, app_name, 'enabled')


def disable(browser, app_name):
    interface.nav_to_module(browser, get_app_module(app_name))
    _change_app_status(browser, app_name, 'disabled')


def wait_for_config_update(browser, app_name):
    while browser.is_element_present_by_css('.running-status.loading'):
        sleep(0.1)


def _download_file(browser, url):
    """Return file contents after downloading a URL."""
    cookies = browser.cookies.all()
    response = requests.get(url, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise Exception('URL download failed')

    return response.content


def select_domain_name(browser, app_name, domain_name):
    browser.visit('{}/plinth/apps/{}/setup/'.format(default_url, app_name))
    drop_down = browser.find_by_id('id_domain_name')
    drop_down.select(domain_name)
    interface.submit(browser, form_class='form-configuration')


def configure_shadowsocks(browser, server, password):
    """Configure shadowsocks client with given server details."""
    browser.visit('{}/plinth/apps/shadowsocks/'.format(default_url))
    browser.find_by_id('id_server').fill(server)
    browser.find_by_id('id_password').fill(password)
    interface.submit(browser, form_class='form-configuration')


def shadowsocks_get_configuration(browser):
    """Return the server and password currently configured in shadowsocks."""
    browser.visit('{}/plinth/apps/shadowsocks/'.format(default_url))
    server = browser.find_by_id('id_server').value
    password = browser.find_by_id('id_password').value
    return server, password


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


def make_share_public(browser, name):
    """Make share publicly accessible."""
    row = get_share(browser, name)
    with wait_for_page_update(browser):
        row.find_by_css('.share-edit')[0].click()
    browser.find_by_id('id_sharing-is_public').check()
    interface.submit(browser)


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
    _change_status(browser, 'mediawiki', 'id_enable_public_registrations',
                   'enabled')


def disable_mediawiki_public_registrations(browser):
    """Enable public registrations in MediaWiki."""
    interface.nav_to_module(browser, 'mediawiki')
    _change_status(browser, 'mediawiki', 'id_enable_public_registrations',
                   'disabled')


def enable_mediawiki_private_mode(browser):
    """Enable public registrations in MediaWiki."""
    interface.nav_to_module(browser, 'mediawiki')
    _change_status(browser, 'mediawiki', 'id_enable_private_mode', 'enabled')


def disable_mediawiki_private_mode(browser):
    """Enable public registrations in MediaWiki."""
    interface.nav_to_module(browser, 'mediawiki')
    _change_status(browser, 'mediawiki', 'id_enable_private_mode', 'disabled')


def set_mediawiki_admin_password(browser, password):
    """Set a password for the MediaWiki user called admin."""
    interface.nav_to_module(browser, 'mediawiki')
    browser.find_by_id('id_password').fill(password)
    interface.submit(browser, form_class='form-configuration')


def enable_ejabberd_message_archive_management(browser):
    """Enable Message Archive Management in Ejabberd."""
    interface.nav_to_module(browser, 'ejabberd')
    _change_status(browser, 'ejabberd', 'id_MAM_enabled', 'enabled')


def disable_ejabberd_message_archive_management(browser):
    """Enable Message Archive Management in Ejabberd."""
    interface.nav_to_module(browser, 'ejabberd')
    _change_status(browser, 'ejabberd', 'id_MAM_enabled', 'disabled')


def ejabberd_add_contact(browser):
    """Add a contact to Ejabberd user's roster."""
    site.jsxc_add_contact(browser)


def ejabberd_delete_contact(browser):
    """Delete the contact from Ejabberd user's roster."""
    site.jsxc_delete_contact(browser)


def ejabberd_has_contact(browser):
    """Check whether the contact is in Ejabberd user's roster."""
    return eventually(site.jsxc_has_contact, [browser])


def gitweb_create_repo(browser, repo, access=None, ok_if_exists=False):
    """Create repository."""
    if not gitweb_repo_exists(browser, repo, access):
        gitweb_delete_repo(browser, repo, ignore_missing=True)
        browser.find_link_by_href('/plinth/apps/gitweb/create/').first.click()
        browser.find_by_id('id_gitweb-name').fill(repo)
        if access == 'private':
            browser.find_by_id('id_gitweb-is_private').check()
        elif access == 'public':
            browser.find_by_id('id_gitweb-is_private').uncheck()
        submit(browser)
    elif not ok_if_exists:
        assert False, 'Repo already exists.'


def gitweb_delete_repo(browser, repo, ignore_missing=False):
    """Delete repository."""
    interface.nav_to_module(browser, 'gitweb')
    delete_link = browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/delete/'.format(repo))
    if delete_link or not ignore_missing:
        delete_link.first.click()
        submit(browser)


def gitweb_edit_repo_metadata(browser, repo, metadata):
    """Set repository metadata."""
    interface.nav_to_module(browser, 'gitweb')
    browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    if 'name' in metadata:
        browser.find_by_id('id_gitweb-name').fill(metadata['name'])
    if 'description' in metadata:
        browser.find_by_id('id_gitweb-description').fill(
            metadata['description'])
    if 'owner' in metadata:
        browser.find_by_id('id_gitweb-owner').fill(metadata['owner'])
    if 'access' in metadata:
        if metadata['access'] == 'private':
            browser.find_by_id('id_gitweb-is_private').check()
        else:
            browser.find_by_id('id_gitweb-is_private').uncheck()
    submit(browser)


def gitweb_get_repo_metadata(browser, repo):
    """Get repository metadata."""
    interface.nav_to_module(browser, 'gitweb')
    browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    metadata = {}
    for item in ['name', 'description', 'owner']:
        metadata[item] = browser.find_by_id('id_gitweb-' + item).value
    if browser.find_by_id('id_gitweb-is_private').value:
        metadata['access'] = 'private'
    else:
        metadata['access'] = 'public'
    return metadata


def _gitweb_get_repo_url(repo, with_auth):
    """"Get repository URL"""
    scheme = 'http'
    if default_url.startswith('https://'):
        scheme = 'https'
    url = default_url.split('://')[1] if '://' in default_url else default_url
    password = 'gitweb_wrong_password'
    if with_auth:
        password = config['DEFAULT']['password']

    return '{0}://{1}:{2}@{3}/gitweb/{4}'.format(scheme,
                                                 config['DEFAULT']['username'],
                                                 password, url, repo)


@contextlib.contextmanager
def _gitweb_temp_directory():
    """Create temporary directory"""
    name = tempfile.mkdtemp(prefix='plinth_test_gitweb_')
    yield name
    shutil.rmtree(name)


def _gitweb_git_command_is_successful(command, cwd):
    """Check if a command runs successfully or gives authentication error"""
    process = subprocess.run(command, capture_output=True, cwd=cwd)
    if process.returncode != 0:
        if 'Authentication failed' in process.stderr.decode():
            return False
        print(process.stdout.decode())
        # raise exception
        process.check_returncode()
    return True


def gitweb_repo_exists(browser, repo, access=None):
    """Check whether the repository exists."""
    interface.nav_to_module(browser, 'gitweb')
    links_found = browser.find_link_by_href('/gitweb/{}.git'.format(repo))
    access_matches = True
    if links_found and access:
        parent = links_found.first.find_by_xpath('..').first
        private_icon = parent.find_by_css('.repo-private-icon')
        if access == 'private':
            access_matches = True if private_icon else False
        if access == 'public':
            access_matches = True if not private_icon else False
    return bool(links_found) and access_matches


def gitweb_repo_is_readable(repo, with_auth=False, url_git_extension=False):
    """Check if a git repo is readable with git client."""
    url = _gitweb_get_repo_url(repo, with_auth)
    if url_git_extension:
        url = url + '.git'
    git_command = ['git', 'clone', '-c', 'http.sslverify=false', url]
    with _gitweb_temp_directory() as cwd:
        return _gitweb_git_command_is_successful(git_command, cwd)


def gitweb_repo_is_writable(repo, with_auth=False, url_git_extension=False):
    """Check if a git repo is writable with git client."""
    url = _gitweb_get_repo_url(repo, with_auth)
    if url_git_extension:
        url = url + '.git'

    with _gitweb_temp_directory() as cwd:
        subprocess.run(['mkdir', 'test-project'], check=True, cwd=cwd)
        cwd = os.path.join(cwd, 'test-project')
        prepare_git_repo_commands = [
            'git init -q', 'git config http.sslVerify false',
            'git commit -q --allow-empty --author "Tester <>" -m "test"'
        ]
        for command in prepare_git_repo_commands:
            subprocess.run(command, shell=True, check=True, cwd=cwd)
        git_push_command = ['git', 'push', '-qf', url, 'master']

        return _gitweb_git_command_is_successful(git_push_command, cwd)


def gitweb_set_repo_access(browser, repo, access):
    """Set repository as public or private."""
    interface.nav_to_module(browser, 'gitweb')
    browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    if access == 'private':
        browser.find_by_id('id_gitweb-is_private').check()
    else:
        browser.find_by_id('id_gitweb-is_private').uncheck()
    submit(browser)


def gitweb_set_all_repos_private(browser):
    """Set all repositories private"""
    interface.nav_to_module(browser, 'gitweb')
    public_repos = []
    for element in browser.find_by_css('#gitweb-repo-list .list-group-item'):
        if not element.find_by_css('.repo-private-icon'):
            repo = element.find_by_css('.repo-label').first.text
            public_repos.append(repo)
    for repo in public_repos:
        gitweb_set_repo_access(browser, repo, 'private')


def gitweb_site_repo_exists(browser, repo):
    """Check whether the repository exists on Gitweb site."""
    browser.visit('{}/gitweb'.format(default_url))
    return browser.find_by_css('a[href="/gitweb/{0}.git"]'.format(repo))


def ikiwiki_create_wiki_if_needed(browser):
    """Create wiki if it does not exist."""
    interface.nav_to_module(browser, 'ikiwiki')
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
    browser.find_link_by_href(
        '/plinth/apps/ikiwiki/wiki/delete/').first.click()
    submit(browser)


def ikiwiki_wiki_exists(browser):
    """Check whether the wiki exists."""
    interface.nav_to_module(browser, 'ikiwiki')
    wiki = browser.find_link_by_href('/ikiwiki/wiki')
    return bool(wiki)


def time_zone_set(browser, time_zone):
    """Set the system time zone."""
    interface.nav_to_module(browser, 'datetime')
    browser.select('time_zone', time_zone)
    interface.submit(browser, form_class='form-configuration')


def time_zone_get(browser):
    """Set the system time zone."""
    interface.nav_to_module(browser, 'datetime')
    return browser.find_by_name('time_zone').first.value


_TOR_FEATURE_TO_ELEMENT = {
    'relay': 'tor-relay_enabled',
    'bridge-relay': 'tor-bridge_relay_enabled',
    'hidden-services': 'tor-hs_enabled',
    'software': 'tor-apt_transport_tor_enabled'
}


def tor_feature_enable(browser, feature, should_enable):
    """Enable/disable a Tor feature."""
    if not isinstance(should_enable, bool):
        should_enable = should_enable in ('enable', 'enabled')

    element_name = _TOR_FEATURE_TO_ELEMENT[feature]
    interface.nav_to_module(browser, 'tor')
    checkbox_element = browser.find_by_name(element_name).first
    if should_enable == checkbox_element.checked:
        return

    if should_enable:
        if feature == 'bridge-relay':
            browser.find_by_name('tor-relay_enabled').first.check()

        checkbox_element.check()
    else:
        checkbox_element.uncheck()

    interface.submit(browser, form_class='form-configuration')
    wait_for_config_update(browser, 'tor')


def tor_assert_feature_enabled(browser, feature, enabled):
    """Assert whether Tor relay is enabled or disabled."""
    if not isinstance(enabled, bool):
        enabled = enabled in ('enable', 'enabled')

    element_name = _TOR_FEATURE_TO_ELEMENT[feature]
    interface.nav_to_module(browser, 'tor')
    assert browser.find_by_name(element_name).first.checked == enabled


def tor_get_relay_ports(browser):
    """Return the list of ports shown in the relay table."""
    interface.nav_to_module(browser, 'tor')
    return [
        port_name.text
        for port_name in browser.find_by_css('.tor-relay-port-name')
    ]


def tor_assert_hidden_services(browser):
    """Assert that hidden service information is shown."""
    interface.nav_to_module(browser, 'tor')
    assert browser.find_by_css('.tor-hs .tor-hs-hostname')


def tahoe_get_introducer(browser, domain, introducer_type):
    """Return an introducer element with a given type from tahoe-lafs."""
    interface.nav_to_module(browser, 'tahoe')
    css_class = '.{}-introducers .introducer-furl'.format(introducer_type)
    for furl in browser.find_by_css(css_class):
        if domain in furl.text:
            return furl.parent

    return None


def tahoe_add_introducer(browser, domain):
    """Add a new introducer into tahoe-lafs."""
    interface.nav_to_module(browser, 'tahoe')

    furl = 'pb://ewe4zdz6kxn7xhuvc7izj2da2gpbgeir@tcp:{}:3456/' \
           'fko4ivfwgqvybppwar3uehkx6spaaou7'.format(domain)
    browser.fill('pet_name', 'testintroducer')
    browser.fill('furl', furl)
    submit(browser, form_class='form-add-introducer')


def tahoe_remove_introducer(browser, domain):
    """Remove an introducer from tahoe-lafs."""
    introducer = tahoe_get_introducer(browser, domain, 'connected')
    submit(browser, element=introducer.find_by_css('.form-remove'))


def radicale_get_access_rights(browser):
    access_rights_types = ['owner_only', 'owner_write', 'authenticated']
    interface.nav_to_module(browser, 'radicale')
    for access_rights_type in access_rights_types:
        if browser.find_by_value(access_rights_type).checked:
            return access_rights_type


def radicale_set_access_rights(browser, access_rights_type):
    interface.nav_to_module(browser, 'radicale')
    browser.choose('access_rights', access_rights_type)
    interface.submit(browser, form_class='form-configuration')


def openvpn_setup(browser):
    """Setup the OpenVPN application after installation."""
    interface.nav_to_module(browser, 'openvpn')
    setup_form = browser.find_by_css('.form-setup')
    if not setup_form:
        return

    submit(browser, form_class='form-setup')
    wait_for_config_update(browser, 'openvpn')


def openvpn_download_profile(browser):
    """Download the current user's profile into a file and return path."""
    interface.nav_to_module(browser, 'openvpn')
    url = browser.find_by_css('.form-profile')['action']
    return _download_file(browser, url)


def samba_set_share(browser, share_type, status='enabled'):
    """Enable or disable samba share."""
    disk_name = 'disk'
    share_type_name = '{0}_share'.format(share_type)
    interface.nav_to_module(browser, 'samba')
    for elem in browser.find_by_tag('td'):
        if elem.text == disk_name:
            share_form = elem.find_by_xpath('(..//*)[2]/form').first
            share_btn = share_form.find_by_name(share_type_name).first
            if status == 'enabled' and share_btn['value'] == 'enable':
                share_btn.click()
            elif status == 'disabled' and share_btn['value'] == 'disable':
                share_btn.click()
            break


def _samba_write_to_share(share_type, as_guest=False):
    """Write to the samba share, return output messages as string."""
    disk_name = 'disk'
    if share_type == 'open':
        share_name = disk_name
    else:
        share_name = '{0}_{1}'.format(disk_name, share_type)
    hostname = urllib.parse.urlparse(default_url).hostname
    servicename = '\\\\{0}\\{1}'.format(hostname, share_name)
    directory = '_plinth-test_{0}'.format(''.join(
        random.SystemRandom().choices(string.ascii_letters, k=8)))
    port = config['DEFAULT']['samba_port']

    smb_command = ['smbclient', '-W', 'WORKGROUP', '-p', port]
    if as_guest:
        smb_command += ['-N']
    else:
        smb_command += [
            '-U', '{0}%{1}'.format(config['DEFAULT']['username'],
                                   config['DEFAULT']['password'])
        ]
    smb_command += [
        servicename, '-c', 'mkdir {0}; rmdir {0}'.format(directory)
    ]

    return subprocess.check_output(smb_command).decode()


def samba_assert_share_is_writable(share_type, as_guest=False):
    """Assert that samba share is writable."""
    output = _samba_write_to_share(share_type, as_guest=False)

    assert not output, output


def samba_assert_share_is_not_accessible(share_type, as_guest=False):
    """Assert that samba share is not accessible."""
    try:
        _samba_write_to_share(share_type, as_guest)
    except subprocess.CalledProcessError as err:
        err_output = err.output.decode()
        assert 'NT_STATUS_ACCESS_DENIED' in err_output, err_output
    else:
        assert False, 'Can access the share.'


def samba_assert_share_is_not_available(share_type):
    """Assert that samba share is not accessible."""
    try:
        _samba_write_to_share(share_type)
    except subprocess.CalledProcessError as err:
        err_output = err.output.decode()
        assert 'NT_STATUS_BAD_NETWORK_NAME' in err_output, err_output
    else:
        assert False, 'Can access the share.'


def searx_enable_public_access(browser):
    """Enable Public Access in SearX"""
    interface.nav_to_module(browser, 'searx')
    browser.find_by_id('id_public_access').check()
    interface.submit(browser, form_class='form-configuration')


def searx_disable_public_access(browser):
    """Enable Public Access in SearX"""
    interface.nav_to_module(browser, 'searx')
    browser.find_by_id('id_public_access').uncheck()
    interface.submit(browser, form_class='form-configuration')


def find_on_front_page(browser, app_name):
    browser.visit(default_url)
    shortcuts = browser.find_link_by_href(f'/{app_name}/')
    return shortcuts
