# SPDX-License-Identifier: AGPL-3.0-or-later

from pytest_bdd import given, parsers, then, when

from support import interface, site


@then(parsers.parse('the {site_name:w} site should be available'))
def site_should_be_available(session_browser, site_name):
    assert site.is_available(session_browser, site_name)


@then(parsers.parse('the {site_name:w} site should not be available'))
def site_should_not_be_available(session_browser, site_name):
    assert not site.is_available(session_browser, site_name)


@when(parsers.parse('I access {app_name:w} application'))
def access_application(session_browser, app_name):
    site.access_url(session_browser, app_name)


@when(
    parsers.parse(
        'I upload an image named {image:S} to mediawiki with credentials {username:w} and '
        '{password:w}'))
def upload_image(session_browser, username, password, image):
    site.upload_image_mediawiki(session_browser, username, password, image)


@then(parsers.parse('there should be {image:S} image'))
def uploaded_image_should_be_available(session_browser, image):
    uploaded_image = site.get_uploaded_image_in_mediawiki(
        session_browser, image)
    assert image.lower() == uploaded_image.lower()


@then(
    parsers.parse(
        'I should be able to login to coquelicot with password {password:w}'))
def verify_upload_password(session_browser, password):
    site.verify_coquelicot_upload_password(session_browser, password)


@when(
    parsers.parse(
        'I upload the sample local file to coquelicot with password {password:w}'
    ))
def coquelicot_upload_file(session_browser, sample_local_file, password):
    url = site.upload_file_to_coquelicot(session_browser,
                                         sample_local_file['file_path'],
                                         password)
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
def mediawiki_allows_creating_accounts(session_browser):
    site.verify_mediawiki_create_account_link(session_browser)


@then(parsers.parse('the mediawiki site should not allow creating accounts'))
def mediawiki_does_not_allow_creating_accounts(session_browser):
    site.verify_mediawiki_no_create_account_link(session_browser)


@then(
    parsers.parse('the mediawiki site should allow anonymous reads and writes')
)
def mediawiki_allows_anonymous_reads_edits(session_browser):
    site.verify_mediawiki_anonymous_reads_edits_link(session_browser)


@then(
    parsers.parse(
        'the mediawiki site should not allow anonymous reads and writes'))
def mediawiki_does_not_allow__account_creation_anonymous_reads_edits(
        session_browser):
    site.verify_mediawiki_no_anonymous_reads_edits_link(session_browser)


@then(
    parsers.parse(
        'I should see the Upload File option in the side pane when logged in '
        'with credentials {username:w} and {password:w}'))
def login_to_mediawiki_with_credentials(session_browser, username, password):
    site.login_to_mediawiki_with_credentials(session_browser, username,
                                             password)


@when('I delete the mediawiki main page')
def mediawiki_delete_main_page(session_browser):
    site.mediawiki_delete_main_page(session_browser)


@then('the mediawiki main page should be restored')
def mediawiki_verify_text(session_browser):
    assert site.mediawiki_has_main_page(session_browser)


@when('all ed2k files are removed from mldonkey')
def mldonkey_remove_all_ed2k_files(session_browser):
    site.mldonkey_remove_all_ed2k_files(session_browser)


@when('I upload a sample ed2k file to mldonkey')
def mldonkey_upload_sample_ed2k_file(session_browser):
    site.mldonkey_upload_sample_ed2k_file(session_browser)


@then(
    parsers.parse(
        'there should be {ed2k_files_number:d} ed2k files listed in mldonkey'))
def mldonkey_assert_number_of_ed2k_files(session_browser, ed2k_files_number):
    assert ed2k_files_number == site.mldonkey_get_number_of_ed2k_files(
        session_browser)


@when('all torrents are removed from transmission')
def transmission_remove_all_torrents(session_browser):
    site.transmission_remove_all_torrents(session_browser)


@when('I upload a sample torrent to transmission')
def transmission_upload_sample_torrent(session_browser):
    site.transmission_upload_sample_torrent(session_browser)


@then(
    parsers.parse(
        'there should be {torrents_number:d} torrents listed in transmission'))
def transmission_assert_number_of_torrents(session_browser, torrents_number):
    assert torrents_number == site.transmission_get_number_of_torrents(
        session_browser)


@when('all torrents are removed from deluge')
def deluge_remove_all_torrents(session_browser):
    site.deluge_remove_all_torrents(session_browser)


@when('I upload a sample torrent to deluge')
def deluge_upload_sample_torrent(session_browser):
    site.deluge_upload_sample_torrent(session_browser)


@then(
    parsers.parse(
        'there should be {torrents_number:d} torrents listed in deluge'))
def deluge_assert_number_of_torrents(session_browser, torrents_number):
    assert torrents_number == site.deluge_get_number_of_torrents(
        session_browser)


@then('the calendar should be available')
def assert_calendar_is_available(session_browser):
    assert site.calendar_is_available(session_browser)


@then('the calendar should not be available')
def assert_calendar_is_not_available(session_browser):
    assert not site.calendar_is_available(session_browser)


@then('the addressbook should be available')
def assert_addressbook_is_available(session_browser):
    assert site.addressbook_is_available(session_browser)


@then('the addressbook should not be available')
def assert_addressbook_is_not_available(session_browser):
    assert not site.addressbook_is_available(session_browser)


@given(parsers.parse('syncthing folder {folder_name:w} is not present'))
def syncthing_folder_not_present(session_browser, folder_name):
    if site.syncthing_folder_is_present(session_browser, folder_name):
        site.syncthing_remove_folder(session_browser, folder_name)


@given(
    parsers.parse(
        'folder {folder_path:S} is present as syncthing folder {folder_name:w}'
    ))
def syncthing_folder_present(session_browser, folder_name, folder_path):
    if not site.syncthing_folder_is_present(session_browser, folder_name):
        site.syncthing_add_folder(session_browser, folder_name, folder_path)


@when(
    parsers.parse(
        'I add a folder {folder_path:S} as syncthing folder {folder_name:w}'))
def syncthing_add_folder(session_browser, folder_name, folder_path):
    site.syncthing_add_folder(session_browser, folder_name, folder_path)


@when(parsers.parse('I remove syncthing folder {folder_name:w}'))
def syncthing_remove_folder(session_browser, folder_name):
    site.syncthing_remove_folder(session_browser, folder_name)


@then(parsers.parse('syncthing folder {folder_name:w} should be present'))
def syncthing_assert_folder_present(session_browser, folder_name):
    assert site.syncthing_folder_is_present(session_browser, folder_name)


@then(parsers.parse('syncthing folder {folder_name:w} should not be present'))
def syncthing_assert_folder_not_present(session_browser, folder_name):
    assert not site.syncthing_folder_is_present(session_browser, folder_name)


@given('I subscribe to a feed in ttrss')
def ttrss_subscribe(session_browser):
    site.ttrss_subscribe(session_browser)


@when('I unsubscribe from the feed in ttrss')
def ttrss_unsubscribe(session_browser):
    site.ttrss_unsubscribe(session_browser)


@then('I should be subscribed to the feed in ttrss')
def ttrss_assert_subscribed(session_browser):
    assert site.ttrss_is_subscribed(session_browser)
