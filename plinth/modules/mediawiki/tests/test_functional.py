# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mediawiki app.
"""

import pathlib

from pytest_bdd import parsers, scenarios, then, when

from plinth.tests import functional

scenarios('mediawiki.feature')


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
def mediawiki_does_not_allow__account_creation_anonymous_reads_edits(
        session_browser):
    _verify_no_anonymous_reads_edits_link(session_browser)


@then(
    parsers.parse(
        'I should see the Upload File option in the side pane when logged in '
        'with credentials {username:w} and {password:w}'))
def login_to_mediawiki_with_credentials(session_browser, username, password):
    _login_with_credentials(session_browser, username, password)


@when('I delete the mediawiki main page')
def mediawiki_delete_main_page(session_browser):
    _delete_main_page(session_browser)


@then('the mediawiki main page should be restored')
def mediawiki_verify_text(session_browser):
    assert _has_main_page(session_browser)


@when(
    parsers.parse(
        'I upload an image named {image:S} to mediawiki with credentials '
        '{username:w} and {password:w}'))
def upload_image(session_browser, username, password, image):
    _upload_image(session_browser, username, password, image)


@then(parsers.parse('there should be {image:S} image'))
def uploaded_image_should_be_available(session_browser, image):
    uploaded_image = _get_uploaded_image(session_browser, image)
    assert image.lower() == uploaded_image.lower()


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


def _verify_create_account_link(browser):
    functional.visit(browser, '/mediawiki/index.php/Special:CreateAccount')
    assert functional.eventually(browser.is_element_present_by_id,
                                 args=['wpCreateaccount'])


def _verify_no_create_account_link(browser):
    functional.visit(browser, '/mediawiki/index.php/Special:CreateAccount')
    assert functional.eventually(browser.is_element_not_present_by_id,
                                 args=['wpCreateaccount'])


def _verify_anonymous_reads_edits_link(browser):
    functional.visit(browser, '/mediawiki')
    assert functional.eventually(browser.is_element_present_by_id,
                                 args=['ca-nstab-main'])


def _verify_no_anonymous_reads_edits_link(browser):
    functional.visit(browser, '/mediawiki')
    assert functional.eventually(browser.is_element_not_present_by_id,
                                 args=['ca-nstab-main'])
    assert functional.eventually(browser.is_element_present_by_id,
                                 args=['ca-nstab-special'])


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


def _upload_image(browser, username, password, image):
    """Upload an image to MediaWiki. Idempotent."""
    functional.visit(browser, '/mediawiki')
    _login(browser, username, password)

    # Upload file
    functional.visit(browser, '/mediawiki/Special:Upload')
    file_path = pathlib.Path(__file__).parent
    file_path /= '../../../../static/themes/default/img/' + image
    browser.attach_file('wpUploadFile', str(file_path.resolve()))
    functional.submit(browser, element=browser.find_by_name('wpUpload')[0])


def _get_number_of_uploaded_images(browser):
    functional.visit(browser, '/mediawiki/Special:ListFiles')
    return len(browser.find_by_css('.TablePager_col_img_timestamp'))


def _get_uploaded_image(browser, image):
    functional.visit(browser, '/mediawiki/Special:ListFiles')
    elements = browser.find_link_by_partial_href(image)
    return elements[0].value


def _delete_main_page(browser):
    """Delete the mediawiki main page."""
    _login(browser, 'admin', 'whatever123')
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
