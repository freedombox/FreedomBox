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

import pytest
import splinter
from pytest_bdd import given, parsers, then, when

from support import application


@given(parsers.parse('the {app_name:w} application is installed'))
def application_is_installed(browser, app_name):
    application.install(browser, app_name)
    assert (application.is_installed(browser, app_name))


@given(parsers.parse('the {app_name:w} application is enabled'))
def application_is_enabled(browser, app_name):
    application.enable(browser, app_name)


@given(parsers.parse('the {app_name:w} application is disabled'))
def application_is_disabled(browser, app_name):
    application.disable(browser, app_name)


@given(parsers.parse('the network time application is enabled'))
def ntp_is_enabled(browser):
    application.enable(browser, 'ntp')


@given(parsers.parse('the network time application is disabled'))
def ntp_is_disabled(browser):
    application.disable(browser, 'ntp')


@when(parsers.parse('I set the time zone to {time_zone:S}'))
def time_zone_set(browser, time_zone):
    application.time_zone_set(browser, time_zone)


@then(parsers.parse('the time zone should be {time_zone:S}'))
def time_zone_assert(browser, time_zone):
    assert time_zone == application.time_zone_get(browser)


@given(parsers.parse('the service discovery application is enabled'))
def avahi_is_enabled(browser):
    application.enable(browser, 'avahi')


@given(parsers.parse('the service discovery application is disabled'))
def avahi_is_disabled(browser):
    application.disable(browser, 'avahi')


@when(parsers.parse('I enable the {app_name:w} application'))
def enable_application(browser, app_name):
    application.enable(browser, app_name)


@when(parsers.parse('I disable the {app_name:w} application'))
def disable_application(browser, app_name):
    application.disable(browser, app_name)


@when(parsers.parse('I enable the network time application'))
def enable_ntp(browser):
    application.enable(browser, 'ntp')


@when(parsers.parse('I disable the network time application'))
def disable_ntp(browser):
    application.disable(browser, 'ntp')


@when(parsers.parse('I enable the service discovery application'))
def enable_avahi(browser):
    application.enable(browser, 'avahi')


@when(parsers.parse('I disable the service discovery application'))
def disable_avahi(browser):
    application.disable(browser, 'avahi')


@given(
    parsers.parse('the domain name for {app_name:w} is set to {domain_name:S}')
)
def select_domain_name(browser, app_name, domain_name):
    application.select_domain_name(browser, app_name, domain_name)


@given('the shadowsocks application is configured')
def configure_shadowsocks(browser):
    application.configure_shadowsocks(browser, 'example.com',
                                      'fakepassword')


@when(
    parsers.parse(
        'I configure shadowsocks with server {server:S} and password {password:w}'
    ))
def configure_shadowsocks_with_details(browser, server, password):
    application.configure_shadowsocks(browser, server, password)


@then(
    parsers.parse(
        'shadowsocks should be configured with server {server:S} and password {password:w}'
    ))
def assert_shadowsocks_configuration(browser, server, password):
    assert (server,
            password) == application.shadowsocks_get_configuration(browser)


@when(
    parsers.parse('I modify the maximum file size of coquelicot to {size:d}'))
def modify_max_file_size(browser, size):
    application.modify_max_file_size(browser, size)


@then(parsers.parse('the maximum file size of coquelicot should be {size:d}'))
def assert_max_file_size(browser, size):
    assert application.get_max_file_size(browser) == size


@when(parsers.parse('I modify the coquelicot upload password to {password:w}'))
def modify_upload_password(browser, password):
    application.modify_upload_password(browser, password)


@given(parsers.parse('share {name:w} is not available'))
def remove_share(browser, name):
    application.remove_share(browser, name)


@when(parsers.parse('I add a share {name:w} from path {path} for {group:w}'))
def add_share(browser, name, path, group):
    application.add_share(browser, name, path, group)


@when(
    parsers.parse(
        'I edit share {old_name:w} to {new_name:w} from path {path} for {group:w}'
    ))
def edit_share(browser, old_name, new_name, path, group):
    application.edit_share(browser, old_name, new_name, path, group)


@when(parsers.parse('I remove share {name:w}'))
def remove_share2(browser, name):
    application.remove_share(browser, name)


@when(parsers.parse('I edit share {name:w} to be public'))
def edit_share_public_access(browser, name):
    application.make_share_public(browser, name)


@then(
    parsers.parse(
        'the share {name:w} should be listed from path {path} for {group:w}'))
def verify_share(browser, name, path, group):
    application.verify_share(browser, name, path, group)


@then(parsers.parse('the share {name:w} should not be listed'))
def verify_invalid_share(browser, name):
    with pytest.raises(splinter.exceptions.ElementDoesNotExist):
        application.get_share(browser, name)


@then(parsers.parse('the share {name:w} should be accessible'))
def access_share(browser, name):
    application.access_share(browser, name)


@then(parsers.parse('the share {name:w} should not exist'))
def verify_nonexistant_share(browser, name):
    application.verify_nonexistant_share(browser, name)


@then(parsers.parse('the share {name:w} should not be accessible'))
def verify_inaccessible_share(browser, name):
    application.verify_inaccessible_share(browser, name)


@when(parsers.parse('I enable mediawiki public registrations'))
def enable_mediawiki_public_registrations(browser):
    application.enable_mediawiki_public_registrations(browser)


@when(parsers.parse('I disable mediawiki public registrations'))
def disable_mediawiki_public_registrations(browser):
    application.disable_mediawiki_public_registrations(browser)


@when(parsers.parse('I enable mediawiki private mode'))
def enable_mediawiki_private_mode(browser):
    application.enable_mediawiki_private_mode(browser)


@when(parsers.parse('I disable mediawiki private mode'))
def disable_mediawiki_private_mode(browser):
    application.disable_mediawiki_private_mode(browser)


@when(parsers.parse('I set the mediawiki admin password to {password}'))
def set_mediawiki_admin_password(browser, password):
    application.set_mediawiki_admin_password(browser, password)


@when(parsers.parse('I enable message archive management'))
def mediawiki_enable_archive_management(browser):
    application.enable_ejabberd_message_archive_management(browser)


@when(parsers.parse('I disable message archive management'))
def mediawiki_disable_archive_management(browser):
    application.disable_ejabberd_message_archive_management(browser)


@when('there is an ikiwiki wiki')
def ikiwiki_create_wiki_if_needed(browser):
    application.ikiwiki_create_wiki_if_needed(browser)


@when('I delete the ikiwiki wiki')
def ikiwiki_delete_wiki(browser):
    application.ikiwiki_delete_wiki(browser)


@then('the ikiwiki wiki should be restored')
def ikiwiki_should_exist(browser):
    assert application.ikiwiki_wiki_exists(browser)


@given('I have added a contact to my roster')
def ejabberd_add_contact(browser):
    application.ejabberd_add_contact(browser)


@when('I delete the contact from my roster')
def ejabberd_delete_contact(browser):
    application.ejabberd_delete_contact(browser)


@then('I should have a contact on my roster')
def ejabberd_should_have_contact(browser):
    assert application.ejabberd_has_contact(browser)


@given(parsers.parse('tor relay is {enabled:w}'))
def tor_given_relay_enable(browser, enabled):
    application.tor_feature_enable(browser, 'relay', enabled)


@when(parsers.parse('I {enable:w} tor relay'))
def tor_relay_enable(browser, enable):
    application.tor_feature_enable(browser, 'relay', enable)


@then(parsers.parse('tor relay should be {enabled:w}'))
def tor_assert_relay_enabled(browser, enabled):
    application.tor_assert_feature_enabled(browser, 'relay', enabled)


@then(parsers.parse('tor {port_name:w} port should be displayed'))
def tor_assert_port_displayed(browser, port_name):
    assert port_name in application.tor_get_relay_ports(browser)


@given(parsers.parse('tor bridge relay is {enabled:w}'))
def tor_given_bridge_relay_enable(browser, enabled):
    application.tor_feature_enable(browser, 'bridge-relay', enabled)


@when(parsers.parse('I {enable:w} tor bridge relay'))
def tor_bridge_relay_enable(browser, enable):
    application.tor_feature_enable(browser, 'bridge-relay', enable)


@then(parsers.parse('tor bridge relay should be {enabled:w}'))
def tor_assert_bridge_relay_enabled(browser, enabled):
    application.tor_assert_feature_enabled(browser, 'bridge-relay', enabled)


@given(parsers.parse('tor hidden services are {enabled:w}'))
def tor_given_hidden_services_enable(browser, enabled):
    application.tor_feature_enable(browser, 'hidden-services', enabled)


@when(parsers.parse('I {enable:w} tor hidden services'))
def tor_hidden_services_enable(browser, enable):
    application.tor_feature_enable(browser, 'hidden-services', enable)


@then(parsers.parse('tor hidden services should be {enabled:w}'))
def tor_assert_hidden_services_enabled(browser, enabled):
    application.tor_assert_feature_enabled(browser, 'hidden-services', enabled)


@then(parsers.parse('tor hidden services information should be displayed'))
def tor_assert_hidden_services(browser):
    application.tor_assert_hidden_services(browser)


@given(parsers.parse('download software packages over tor is {enabled:w}'))
def tor_given_download_software_over_tor_enable(browser, enabled):
    application.tor_feature_enable(browser, 'software', enabled)


@when(parsers.parse('I {enable:w} download software packages over tor'))
def tor_download_software_over_tor_enable(browser, enable):
    application.tor_feature_enable(browser, 'software', enable)


@then(
    parsers.parse('download software packages over tor should be {enabled:w}'))
def tor_assert_download_software_over_tor(browser, enabled):
    application.tor_assert_feature_enabled(browser, 'software', enabled)


@then(
    parsers.parse(
        '{domain:S} should be a tahoe {introducer_type:w} introducer'))
def tahoe_assert_introducer(browser, domain, introducer_type):
    assert application.tahoe_get_introducer(browser, domain, introducer_type)


@then(
    parsers.parse(
        '{domain:S} should not be a tahoe {introducer_type:w} introducer'))
def tahoe_assert_not_introducer(browser, domain, introducer_type):
    assert not application.tahoe_get_introducer(browser, domain,
                                                introducer_type)


@given(parsers.parse('{domain:S} is not a tahoe introducer'))
def tahoe_given_remove_introducer(browser, domain):
    if application.tahoe_get_introducer(browser, domain, 'connected'):
        application.tahoe_remove_introducer(browser, domain)


@when(parsers.parse('I add {domain:S} as a tahoe introducer'))
def tahoe_add_introducer(browser, domain):
    application.tahoe_add_introducer(browser, domain)


@given(parsers.parse('{domain:S} is a tahoe introducer'))
def tahoe_given_add_introducer(browser, domain):
    if not application.tahoe_get_introducer(browser, domain, 'connected'):
        application.tahoe_add_introducer(browser, domain)


@when(parsers.parse('I remove {domain:S} as a tahoe introducer'))
def tahoe_remove_introducer(browser, domain):
    application.tahoe_remove_introducer(browser, domain)

@given('the access rights are set to "only the owner can view or make changes"')
def radicale_given_owner_only(browser):
    application.radicale_set_access_rights(browser, 'owner_only')

@given('the access rights are set to "any user can view, but only the owner can make changes"')
def radicale_given_owner_write(browser):
    application.radicale_set_access_rights(browser, 'owner_write')

@given('the access rights are set to "any user can view or make changes"')
def radicale_given_authenticated(browser):
    application.radicale_set_access_rights(browser, 'authenticated')

@when('I change the access rights to "only the owner can view or make changes"')
def radicale_set_owner_only(browser):
    application.radicale_set_access_rights(browser, 'owner_only')

@when('I change the access rights to "any user can view, but only the owner can make changes"')
def radicale_set_owner_write(browser):
    application.radicale_set_access_rights(browser, 'owner_write')

@when('I change the access rights to "any user can view or make changes"')
def radicale_set_authenticated(browser):
    application.radicale_set_access_rights(browser, 'authenticated')

@then('the access rights should be "only the owner can view or make changes"')
def radicale_check_owner_only(browser):
    assert application.radicale_get_access_rights(browser) == 'owner_only'

@then('the access rights should be "any user can view, but only the owner can make changes"')
def radicale_check_owner_write(browser):
    assert application.radicale_get_access_rights(browser) == 'owner_write'

@then('the access rights should be "any user can view or make changes"')
def radicale_check_authenticated(browser):
    assert application.radicale_get_access_rights(browser) == 'authenticated'


@given(parsers.parse('the openvpn application is setup'))
def openvpn_setup(browser):
    application.openvpn_setup(browser)


@given('I download openvpn profile')
def openvpn_download_profile(browser):
    return application.openvpn_download_profile(browser)


@then('the openvpn profile should be downloadable')
def openvpn_profile_downloadable(browser):
    application.openvpn_download_profile(browser)


@then('the openvpn profile downloaded should be same as before')
def openvpn_profile_download_compare(browser, openvpn_download_profile):
    new_profile = application.openvpn_download_profile(browser)
    assert openvpn_download_profile == new_profile


@given('public access is enabled in searx')
def searx_public_access_enabled(browser):
    application.searx_enable_public_access(browser)


@when('I enable public access in searx')
def searx_enable_public_access(browser):
    application.searx_enable_public_access(browser)


@when('I disable public access in searx')
def searx_disable_public_access(browser):
    application.searx_disable_public_access(browser)


@then(parsers.parse('{app_name:w} app should be visible on the front page'))
def app_visible_on_front_page(browser, app_name):
    shortcuts = application.find_on_front_page(browser, app_name)
    assert len(shortcuts) == 1


@then(
    parsers.parse('{app_name:w} app should not be visible on the front page'))
def app_not_visible_on_front_page(browser, app_name):
    shortcuts = application.find_on_front_page(browser, app_name)
    assert len(shortcuts) == 0


@given('a public repository')
@given('a repository')
@given('at least one repository exists')
def gitweb_repo(browser):
    application.gitweb_create_repo(browser, 'Test-repo', 'public', True)


@given('a private repository')
def gitweb_private_repo(browser):
    application.gitweb_create_repo(browser, 'Test-repo', 'private', True)


@given('both public and private repositories exist')
def gitweb_public_and_private_repo(browser):
    application.gitweb_create_repo(browser, 'Test-repo', 'public', True)
    application.gitweb_create_repo(browser, 'Test-repo2', 'private', True)


@given(parsers.parse("a {access:w} repository that doesn't exist"))
def gitweb_nonexistent_repo(browser, access):
    application.gitweb_delete_repo(browser, 'Test-repo', ignore_missing=True)
    return dict(access=access)


@given('all repositories are private')
def gitweb_all_repositories_private(browser):
    application.gitweb_set_all_repos_private(browser)


@given(parsers.parse('a repository metadata:\n{metadata}'))
def gitweb_repo_metadata(browser, metadata):
    metadata_dict = {}
    for item in metadata.split('\n'):
        item = item.split(': ')
        metadata_dict[item[0]] = item[1]
    return metadata_dict


@when('I create the repository')
def gitweb_create_repo(browser, access):
    application.gitweb_create_repo(browser, 'Test-repo', access)


@when('I delete the repository')
def gitweb_delete_repo(browser):
    application.gitweb_delete_repo(browser, 'Test-repo')


@when('I set the metadata of the repository')
def gitweb_edit_repo_metadata(browser, gitweb_repo_metadata):
    application.gitweb_edit_repo_metadata(browser, 'Test-repo',
                                          gitweb_repo_metadata)


@when('using a git client')
def gitweb_using_git_client():
    pass


@then('the repository should be restored')
@then('the repository should be listed as a public')
def gitweb_repo_should_exists(browser):
    assert application.gitweb_repo_exists(browser, 'Test-repo',
                                          access='public')


@then('the repository should be listed as a private')
def gitweb_private_repo_should_exists(browser):
    assert application.gitweb_repo_exists(browser, 'Test-repo', 'private')


@then('the repository should not be listed')
def gitweb_repo_should_not_exist(browser, gitweb_repo):
    assert not application.gitweb_repo_exists(browser, gitweb_repo)


@then('the public repository should be listed on gitweb')
@then('the repository should be listed on gitweb')
def gitweb_repo_should_exist_on_gitweb(browser):
    assert application.gitweb_site_repo_exists(browser, 'Test-repo')


@then('the private repository should not be listed on gitweb')
def gitweb_private_repo_should_exists_on_gitweb(browser):
    assert not application.gitweb_site_repo_exists(browser, 'Test-repo2')


@then('the metadata of the repository should be as set')
def gitweb_repo_metadata_should_match(browser, gitweb_repo_metadata):
    actual_metadata = application.gitweb_get_repo_metadata(
        browser, 'Test-repo')
    assert all(item in actual_metadata.items()
               for item in gitweb_repo_metadata.items())


@then('the repository should be publicly readable')
def gitweb_repo_publicly_readable():
    assert application.gitweb_repo_is_readable('Test-repo')
    assert application.gitweb_repo_is_readable('Test-repo',
                                               url_git_extension=True)


@then('the repository should not be publicly readable')
def gitweb_repo_not_publicly_readable():
    assert not application.gitweb_repo_is_readable('Test-repo')
    assert not application.gitweb_repo_is_readable('Test-repo',
                                                   url_git_extension=True)


@then('the repository should not be publicly writable')
def gitweb_repo_not_publicly_writable():
    assert not application.gitweb_repo_is_writable('Test-repo')
    assert not application.gitweb_repo_is_writable('Test-repo',
                                                   url_git_extension=True)


@then('the repository should be privately readable')
def gitweb_repo_privately_readable():
    assert application.gitweb_repo_is_readable('Test-repo', with_auth=True)
    assert application.gitweb_repo_is_readable('Test-repo', with_auth=True,
                                               url_git_extension=True)


@then('the repository should be privately writable')
def gitweb_repo_privately_writable():
    assert application.gitweb_repo_is_writable('Test-repo', with_auth=True)
    assert application.gitweb_repo_is_writable('Test-repo', with_auth=True,
                                               url_git_extension=True)
