# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mediawiki app.
"""

import pathlib
from urllib.parse import urlparse

import requests
from plinth.tests import functional
from plinth.tests.functional import config
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('mediawiki.feature')


@given(parsers.parse('the server url is set to test config url'))
def set_server_url(session_browser):
    _set_server_url(session_browser)


@when(parsers.parse('I enable mediawiki public registrations'))
def enable_mediawiki_public_registrations(session_browser):
    _enable_public_registrations(session_browser)


@when(parsers.parse('I disable mediawiki public registrations'))
def disable_mediawiki_public_registrations(session_browser):
    _disable_public_registrations(session_browser)


@when(parsers.parse('I enable mediawiki private mode'))
def enable_mediawiki_private_mode(session_browser):
    _enable_private_mode(session_browser)


@when(parsers.parse('I disable mediawiki private mode'))
def disable_mediawiki_private_mode(session_browser):
    _disable_private_mode(session_browser)


@when(parsers.parse('I set the mediawiki admin password to {password}'))
def set_mediawiki_admin_password(session_browser, password):
    _set_admin_password(session_browser, password)


@then(parsers.parse('the mediawiki site should allow creating accounts'))
def mediawiki_allows_creating_accounts(session_browser):
    _verify_create_account_link(session_browser)


@then(parsers.parse('the mediawiki site should not allow creating accounts'))
def mediawiki_does_not_allow_creating_accounts(session_browser):
    _verify_no_create_account_link(session_browser)


@then(
    parsers.parse('the mediawiki site should allow anonymous reads and writes')
)
def mediawiki_allows_anonymous_reads_edits(session_browser):
    _verify_anonymous_reads_edits_link(session_browser)


@then(
    parsers.parse(
        'the mediawiki site should not allow anonymous reads and writes'))
def mediawiki_does_not_allow_anonymous_reads_edits(session_browser):
    _verify_no_anonymous_reads_edits_link(session_browser)


@then(
    parsers.parse(
        'I should see the Upload File option in the side pane when logged in '
        'with credentials {username:w} and {password:w}'))
def login_to_mediawiki_with_credentials(session_browser, username, password):
    _login_with_credentials(session_browser, username, password)


@when(
    parsers.parse('I delete the mediawiki main page with credentials '
                  '{username:w} and {password:w}'))
def mediawiki_delete_main_page(session_browser, username, password):
    _delete_main_page(session_browser, username, password)


@when(
    parsers.parse('I delete {image:S} image with credentials '
                  '{username:w} and {password:w}'))
def delete_image(session_browser, username, password, image):
    _delete_image(session_browser, username, password, image)


@then('the mediawiki main page should be restored')
def mediawiki_verify_text(session_browser):
    assert _has_main_page(session_browser)


@when(
    parsers.parse(
        'I upload an image named {image:S} to mediawiki with credentials '
        '{username:w} and {password:w}'))
def upload_image(session_browser, username, password, image):
    _upload_image(session_browser, username, password, image)


@given(
    parsers.parse('I ensure that there is {image:S} image with credentials '
                  '{username:w} and {password:w}'))
def ensure_image_exists(session_browser, username, password, image):
    if not _image_exists(session_browser, image):
        _upload_image(session_browser, username, password, image)


@then(parsers.parse('there should be {image:S} image'))
def uploaded_image_should_be_available(session_browser, image):
    assert _image_exists(session_browser, image)


def _enable_public_registrations(browser):
    """Enable public registrations in MediaWiki."""
    functional.nav_to_module(browser, 'mediawiki')
    functional.change_checkbox_status(browser, 'mediawiki',
                                      'id_enable_public_registrations',
                                      'enabled')


def _disable_public_registrations(browser):
    """Enable public registrations in MediaWiki."""
    functional.nav_to_module(browser, 'mediawiki')
    functional.change_checkbox_status(browser, 'mediawiki',
                                      'id_enable_public_registrations',
                                      'disabled')


def _enable_private_mode(browser):
    """Enable public registrations in MediaWiki."""
    functional.nav_to_module(browser, 'mediawiki')
    functional.change_checkbox_status(browser, 'mediawiki',
                                      'id_enable_private_mode', 'enabled')


def _disable_private_mode(browser):
    """Enable public registrations in MediaWiki."""
    functional.nav_to_module(browser, 'mediawiki')
    functional.change_checkbox_status(browser, 'mediawiki',
                                      'id_enable_private_mode', 'disabled')


def _set_admin_password(browser, password):
    """Set a password for the MediaWiki user called admin."""
    functional.nav_to_module(browser, 'mediawiki')
    browser.find_by_id('id_password').fill(password)
    functional.submit(browser, form_class='form-configuration')


def _is_create_account_available(browser):
    """Load the create account page and return whether creating is allowed."""
    functional.visit(browser, '/mediawiki/index.php/Special:CreateAccount')
    return browser.is_element_present_by_id('wpCreateaccount')


def _verify_create_account_link(browser):
    assert functional.eventually(_is_create_account_available, args=[browser])


def _verify_no_create_account_link(browser):
    assert functional.eventually(
        lambda: not _is_create_account_available(browser))


def _is_anonymouse_read_allowed(browser):
    """Load the main page and check if anonymous reading is allowed."""
    functional.visit(browser, '/mediawiki')
    return browser.is_element_present_by_id('ca-nstab-main')


def _verify_anonymous_reads_edits_link(browser):
    assert functional.eventually(_is_anonymouse_read_allowed, args=[browser])


def _verify_no_anonymous_reads_edits_link(browser):
    assert functional.eventually(
        lambda: not _is_anonymouse_read_allowed(browser))
    assert browser.is_element_present_by_id('ca-nstab-special')


def _login(browser, username, password):
    functional.visit(browser, '/mediawiki/index.php?title=Special:Login')
    browser.find_by_id('wpName1').fill(username)
    browser.find_by_id('wpPassword1').fill(password)
    with functional.wait_for_page_update(browser):
        browser.find_by_id('wpLoginAttempt').click()


def _login_with_credentials(browser, username, password):
    _login(browser, username, password)
    # Had to put it in the same step because sessions don't
    # persist between steps
    assert functional.eventually(browser.is_element_present_by_id,
                                 args=['t-upload'])


def _upload_image(browser, username, password, image, ignore_warnings=True):
    """Upload an image to MediaWiki. Idempotent."""
    functional.visit(browser, '/mediawiki')
    _login(browser, username, password)

    # Upload file
    functional.visit(browser, '/mediawiki/Special:Upload')
    file_path = pathlib.Path(__file__).parent
    file_path /= '../../../../static/themes/default/img/' + image.lower()
    browser.attach_file('wpUploadFile', str(file_path.resolve()))
    if ignore_warnings:  # allow uploading file with the same name
        browser.find_by_name('wpIgnoreWarning').first.click()
    functional.submit(browser, element=browser.find_by_name('wpUpload')[0])


def _delete_image(browser, username, password, image):
    """Delete an image from MediaWiki."""
    _login(browser, username, password)
    path = f'/mediawiki/index.php?title=File:{image}&action=delete'
    functional.visit(browser, path)
    delete_button = browser.find_by_id('mw-filedelete-submit')
    functional.submit(browser, element=delete_button)


def _get_number_of_uploaded_images(browser):
    functional.visit(browser, '/mediawiki/Special:ListFiles')
    return len(browser.find_by_css('.TablePager_col_img_timestamp'))


def _image_exists(browser, image):
    """Check whether the given image exists."""
    functional.visit(browser, '/mediawiki/Special:ListFiles')
    elements = browser.links.find_by_partial_href(image)
    if not elements:  # Necessary but insufficient check.
        # Special:ListFiles also shows deleted images.
        return False

    # The second hyperlink is a direct link to the image.
    response = requests.get(elements[1]['href'], verify=False)
    return response.status_code != 404


def _delete_main_page(browser, username, password):
    """Delete the mediawiki main page."""
    _login(browser, username, password)
    functional.visit(browser,
                     '/mediawiki/index.php?title=Main_Page&action=delete')
    with functional.wait_for_page_update(browser):
        browser.find_by_id('wpConfirmB').first.click()


def _has_main_page(browser):
    """Check if mediawiki main page exists."""
    return functional.eventually(__has_main_page, [browser])


def __has_main_page(browser):
    """Check if mediawiki main page exists."""
    functional.visit(browser, '/mediawiki/Main_Page')
    content = browser.find_by_id('mw-content-text').first
    return 'This page has been deleted.' not in content.text


def _set_server_url(browser):
    """Set the value of server url to the value in the given env_var."""
    functional.nav_to_module(browser, 'mediawiki')
    server_url = urlparse(config['DEFAULT']['url']).netloc
    browser.find_by_id('id_server_url').fill(server_url)
    functional.submit(browser, form_class='form-configuration')
