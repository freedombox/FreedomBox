# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mediawiki app.
"""

import pathlib
from urllib.parse import urlparse

import requests
import pytest
from plinth.tests import functional
from plinth.tests.functional import config

pytestmark = [pytest.mark.apps, pytest.mark.mediawiki]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'mediawiki')
    _set_server_url(session_browser)
    yield
    functional.app_disable(session_browser, 'mediawiki')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'mediawiki')

    functional.app_enable(session_browser, 'mediawiki')
    assert functional.is_available(session_browser, 'mediawiki')

    functional.app_disable(session_browser, 'mediawiki')
    assert not functional.is_available(session_browser, 'mediawiki')


def test_public_registrations(session_browser):
    """Test enabling public registrations."""
    functional.app_enable(session_browser, 'mediawiki')
    _enable_public_registrations(session_browser)
    _verify_create_account_link(session_browser)

    _disable_public_registrations(session_browser)
    _verify_no_create_account_link(session_browser)


def test_private_mode(session_browser):
    """Test enabling private mode."""
    functional.app_enable(session_browser, 'mediawiki')
    _enable_private_mode(session_browser)
    _verify_no_create_account_link(session_browser)
    _verify_no_anonymous_reads_edits_link(session_browser)

    _disable_private_mode(session_browser)
    _verify_anonymous_reads_edits_link(session_browser)


def test_private_mode_public_registrations(session_browser):
    """Test interactive between private mode and public registrations.

    Requires JS."""
    functional.app_enable(session_browser, 'mediawiki')

    # Enabling private mode disables public registrations
    _enable_public_registrations(session_browser)
    _enable_private_mode(session_browser)
    _verify_no_create_account_link(session_browser)

    # Enabling public registrations disables private mode
    _enable_private_mode(session_browser)
    _enable_public_registrations(session_browser)
    _verify_create_account_link(session_browser)


def test_upload_files(session_browser):
    """Test that logged in user can see upload files option.

    Requires JS."""
    functional.app_enable(session_browser, 'mediawiki')
    _set_admin_password(session_browser, 'whatever123')
    _login_with_credentials(session_browser, 'admin', 'whatever123')


def test_upload_images(session_browser):
    """Test uploading an image."""
    functional.app_enable(session_browser, 'mediawiki')
    _upload_image(session_browser, 'admin', 'whatever123', 'noise.png')
    assert _image_exists(session_browser, 'Noise.png')


def test_upload_svg_image(session_browser):
    """Test uploading an SVG image."""
    functional.app_enable(session_browser, 'mediawiki')
    _upload_image(session_browser, 'admin', 'whatever123',
                  'apps-background.svg')
    assert _image_exists(session_browser, 'Apps-background.svg')


def test_backup_restore(session_browser):
    """Test backup and restore of pages and images."""
    functional.app_enable(session_browser, 'mediawiki')
    if not _image_exists(session_browser, 'Noise.png'):
        _upload_image(session_browser, 'admin', 'whatever123', 'Noise.png')

    functional.backup_create(session_browser, 'mediawiki', 'test_mediawiki')

    _enable_public_registrations(session_browser)
    _delete_image(session_browser, 'admin', 'whatever123', 'Noise.png')
    _delete_main_page(session_browser, 'admin', 'whatever123')
    functional.backup_restore(session_browser, 'mediawiki', 'test_mediawiki')

    assert _has_main_page(session_browser)
    assert _image_exists(session_browser, 'Noise.png')
    _verify_create_account_link(session_browser)


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
