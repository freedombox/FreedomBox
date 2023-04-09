# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mediawiki app.
"""

import pathlib
from urllib.parse import urlparse

import pytest
import requests

from plinth.tests import functional
from plinth.tests.functional import config

pytestmark = [pytest.mark.apps, pytest.mark.mediawiki]


class TestMediawikiApp(functional.BaseAppTests):
    app_name = 'mediawiki'
    has_service = False
    has_web = True

    @pytest.fixture(scope='class', autouse=True)
    def fixture_setup(self, session_browser):
        """Setup the app."""
        functional.login(session_browser)
        functional.install(session_browser, 'mediawiki')
        functional.app_enable(session_browser, 'mediawiki')
        _set_domain(session_browser)
        _set_admin_password(session_browser, 'whatever123')

    @pytest.fixture(name='no_login')
    def fixture_no_login(self, session_browser):
        """Ensure logout from MediaWiki."""
        _logout(session_browser)

    @pytest.fixture(name='login')
    def fixture_login(self, session_browser):
        """Ensure login to MediaWiki."""
        _login_with_credentials(session_browser, 'admin', 'whatever123')

    def test_public_registrations(self, session_browser, no_login):
        """Test enabling public registrations."""
        _enable_public_registrations(session_browser)
        _verify_create_account_link(session_browser)

        _disable_public_registrations(session_browser)
        _verify_no_create_account_link(session_browser)

    def test_private_mode(self, session_browser, no_login):
        """Test enabling private mode."""
        _enable_private_mode(session_browser)
        _verify_no_create_account_link(session_browser)
        _verify_no_anonymous_reads_edits_link(session_browser)

        _disable_private_mode(session_browser)
        _verify_anonymous_reads_edits_link(session_browser)

    def test_private_mode_public_registrations(self, session_browser,
                                               no_login):
        """Test interactive between private mode and public registrations.

        Requires JS."""
        # Enabling private mode disables public registrations
        _enable_public_registrations(session_browser)
        _enable_private_mode(session_browser)
        _verify_no_create_account_link(session_browser)

        # Enabling public registrations disables private mode
        _enable_private_mode(session_browser)
        _enable_public_registrations(session_browser)
        _verify_create_account_link(session_browser)

    def test_upload_images(self, session_browser, login):
        """Test uploading an image."""
        _upload_image(session_browser, 'admin', 'whatever123', 'noise.png')
        assert _image_exists(session_browser, 'Noise.png')

    def test_upload_svg_image(self, session_browser, login):
        """Test uploading an SVG image."""
        _upload_image(session_browser, 'admin', 'whatever123',
                      'apps-background.svg')
        assert _image_exists(session_browser, 'Apps-background.svg')

    def test_backup_restore(self, session_browser, login):
        """Test backup and restore of pages and images."""
        if not _image_exists(session_browser, 'Noise.png'):
            _upload_image(session_browser, 'admin', 'whatever123', 'Noise.png')

        functional.backup_create(session_browser, 'mediawiki',
                                 'test_mediawiki')

        _enable_public_registrations(session_browser)
        _delete_image(session_browser, 'admin', 'whatever123', 'Noise.png')
        _delete_main_page(session_browser, 'admin', 'whatever123')
        functional.backup_restore(session_browser, 'mediawiki',
                                  'test_mediawiki')

        assert _has_main_page(session_browser)
        assert _image_exists(session_browser, 'Noise.png')
        _verify_create_account_link(session_browser)

    def test_uninstall(self, session_browser):
        """Setup the app configuration again after a re-install."""
        super().test_uninstall(session_browser)
        _set_domain(session_browser)
        _set_admin_password(session_browser, 'whatever123')


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


def _is_anonymous_read_allowed(browser):
    """Load the main page and check if anonymous reading is allowed."""
    functional.visit(browser, '/mediawiki')
    return browser.is_element_present_by_id('ca-nstab-main')


def _verify_anonymous_reads_edits_link(browser):
    assert functional.eventually(_is_anonymous_read_allowed, args=[browser])


def _verify_no_anonymous_reads_edits_link(browser):
    assert functional.eventually(
        lambda: not _is_anonymous_read_allowed(browser))
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


def _logout(browser):
    """Logout from MediaWiki."""
    functional.visit(browser, '/mediawiki/Special:UserLogout')
    if browser.find_by_css('#bodyContent form'):
        functional.submit(browser, form_class='oo-ui-formLayout')


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
    if not delete_button:
        # On bookworm and higher
        delete_button = browser.find_by_id('wpConfirmB')

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


def _set_domain(browser):
    """Set the value of domain to the value in the given env_var."""
    functional.nav_to_module(browser, 'mediawiki')
    domain = urlparse(config['DEFAULT']['url']).netloc
    browser.find_by_id('id_domain').fill(domain)
    functional.submit(browser, form_class='form-configuration')
