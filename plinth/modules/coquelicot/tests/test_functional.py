# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for coquelicot app.
"""

import random
import tempfile

from pytest_bdd import given, parsers, scenarios, then, when
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from plinth.tests import functional

scenarios('coquelicot.feature')


@given('a sample local file')
def sample_local_file():
    file_path, contents = _create_sample_local_file()
    return dict(file_path=file_path, contents=contents)


@when(parsers.parse('I modify the maximum file size of coquelicot to {size:d}')
      )
def modify_max_file_size(session_browser, size):
    _modify_max_file_size(session_browser, size)


@then(parsers.parse('the maximum file size of coquelicot should be {size:d}'))
def assert_max_file_size(session_browser, size):
    assert _get_max_file_size(session_browser) == size


@when(parsers.parse('I modify the coquelicot upload password to {password:w}'))
def modify_upload_password(session_browser, password):
    _modify_upload_password(session_browser, password)


@then(
    parsers.parse(
        'I should be able to login to coquelicot with password {password:w}'))
def verify_upload_password(session_browser, password):
    _verify_upload_password(session_browser, password)


@when(
    parsers.parse('I upload the sample local file to coquelicot with password '
                  '{password:w}'))
def coquelicot_upload_file(session_browser, sample_local_file, password):
    url = _upload_file(session_browser, sample_local_file['file_path'],
                       password)
    sample_local_file['upload_url'] = url


@when('I download the uploaded file from coquelicot')
def coquelicot_download_file(sample_local_file):
    file_path = functional.download_file_outside_browser(
        sample_local_file['upload_url'])
    sample_local_file['download_path'] = file_path


@then('contents of downloaded sample file should be same as sample local file')
def coquelicot_compare_upload_download_files(sample_local_file):
    _compare_files(sample_local_file['file_path'],
                   sample_local_file['download_path'])


def _create_sample_local_file():
    """Create a sample file for upload using browser."""
    contents = bytearray(random.getrandbits(8) for _ in range(64))
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(contents)

    return temp_file.name, contents


def _verify_upload_password(browser, password):
    functional.visit(browser, '/coquelicot')
    # ensure the password form is scrolled into view
    browser.execute_script('window.scrollTo(100, 0)')
    browser.find_by_id('upload_password').fill(password)
    actions = ActionChains(browser.driver)
    actions.send_keys(Keys.RETURN)
    actions.perform()
    assert functional.eventually(browser.is_element_present_by_css,
                                 args=['div[style*="display: none;"]'])


def _upload_file(browser, file_path, password):
    """Upload a local file from disk to coquelicot."""
    _verify_upload_password(browser, password)
    browser.attach_file('file', file_path)
    functional.submit(browser)
    assert functional.eventually(browser.is_element_present_by_css,
                                 args=['#content .url'])
    url_textarea = browser.find_by_css('#content .url textarea').first
    return url_textarea.value


def _modify_max_file_size(browser, size):
    """Change the maximum file size of coquelicot to the given value"""
    functional.visit(browser, '/plinth/apps/coquelicot/')
    browser.find_by_id('id_max_file_size').fill(size)
    functional.submit(browser, form_class='form-configuration')


def _get_max_file_size(browser):
    """Get the maximum file size of coquelicot"""
    functional.visit(browser, '/plinth/apps/coquelicot/')
    return int(browser.find_by_id('id_max_file_size').value)


def _modify_upload_password(browser, password):
    """Change the upload password for coquelicot to the given value"""
    functional.visit(browser, '/plinth/apps/coquelicot/')
    browser.find_by_id('id_upload_password').fill(password)
    functional.submit(browser, form_class='form-configuration')


def _compare_files(file1, file2):
    """Assert that the contents of two files are the same."""
    file1_contents = open(file1, 'rb').read()
    file2_contents = open(file2, 'rb').read()

    assert file1_contents == file2_contents
