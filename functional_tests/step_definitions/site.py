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

from pytest_bdd import given, parsers, then, when

from support import interface, site


@then(parsers.parse('the {site_name:w} site should be available'))
def site_should_be_available(browser, site_name):
    assert site.is_available(browser, site_name)


@then(parsers.parse('the {site_name:w} site should not be available'))
def site_should_not_be_available(browser, site_name):
    assert not site.is_available(browser, site_name)


@when(parsers.parse('I access {app_name:w} application'))
def access_application(browser, app_name):
    site.access_url(browser, app_name)


@when(
    parsers.parse(
        'I upload an image named {image:S} to mediawiki with credentials {username:w} and '
        '{password:w}'))
def upload_image(browser, username, password, image):
    site.upload_image_mediawiki(browser, username, password, image)


@then(parsers.parse('there should be {image:S} image'))
def uploaded_image_should_be_available(browser, image):
    uploaded_image = site.get_uploaded_image_in_mediawiki(browser, image)
    assert image.lower() == uploaded_image.lower()


@then(
    parsers.parse(
        'I should be able to login to coquelicot with password {password:w}'))
def verify_upload_password(browser, password):
    site.verify_coquelicot_upload_password(browser, password)


@when(
    parsers.parse(
        'I upload the sample local file to coquelicot with password {password:w}'
    ))
def coquelicot_upload_file(browser, sample_local_file, password):
    url = site.upload_file_to_coquelicot(
        browser, sample_local_file['file_path'], password)
    sample_local_file['upload_url'] = url


@when('I download the uploaded file from coquelicot')
def coquelicot_download_file(sample_local_file):
    file_path = interface.download_file(sample_local_file['upload_url'])
    sample_local_file['download_path'] = file_path


@then('contents of downloaded sample file should be same as sample local file')
def coquelicot_compare_upload_download_files(sample_local_file):
    interface.compare_files(sample_local_file['file_path'],
                            sample_local_file['download_path'])


@then(parsers.parse('the mediawiki site should allow creating accounts'))
def mediawiki_allows_creating_accounts(browser):
    site.verify_mediawiki_create_account_link(browser)


@then(parsers.parse('the mediawiki site should not allow creating accounts'))
def mediawiki_does_not_allow_creating_accounts(browser):
    site.verify_mediawiki_no_create_account_link(browser)


@then(
    parsers.parse('the mediawiki site should allow anonymous reads and writes')
)
def mediawiki_allows_anonymous_reads_edits(browser):
    site.verify_mediawiki_anonymous_reads_edits_link(browser)


@then(
    parsers.parse(
        'the mediawiki site should not allow anonymous reads and writes'))
def mediawiki_does_not_allow__account_creation_anonymous_reads_edits(browser):
    site.verify_mediawiki_no_anonymous_reads_edits_link(browser)


@then(
    parsers.parse(
        'I should see the Upload File option in the side pane when logged in '
        'with credentials {username:w} and {password:w}'))
def login_to_mediawiki_with_credentials(browser, username, password):
    site.login_to_mediawiki_with_credentials(browser, username, password)


@when('I delete the mediawiki main page')
def mediawiki_delete_main_page(browser):
    site.mediawiki_delete_main_page(browser)


@then('the mediawiki main page should be restored')
def mediawiki_verify_text(browser):
    assert site.mediawiki_has_main_page(browser)


@given('repro has been configured')
def repro_configure(browser):
    site.repro_configure(browser)


@when('I delete the repro configuration')
def repro_delete_config(browser):
    site.repro_delete_config(browser)


@then('the repro configuration should be restored')
def repro_is_configured(browser):
    assert site.repro_is_configured(browser)


@when('all torrents are removed from transmission')
def transmission_remove_all_torrents(browser):
    site.transmission_remove_all_torrents(browser)


@when('I upload a sample torrent to transmission')
def transmission_upload_sample_torrent(browser):
    site.transmission_upload_sample_torrent(browser)


@then(
    parsers.parse(
        'there should be {torrents_number:d} torrents listed in transmission'
    ))
def transmission_assert_number_of_torrents(browser, torrents_number):
    assert torrents_number == site.transmission_get_number_of_torrents(browser)
