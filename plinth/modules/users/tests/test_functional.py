# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for users app.
"""

import random
import string
import subprocess
import urllib

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

_admin_password = functional.config['DEFAULT']['password']

scenarios('users.feature')

_language_codes = {
    'None': '',
    'Deutsch': 'de',
    'Nederlands': 'nl',
    'Português': 'pt',
    'Türkçe': 'tr',
    'dansk': 'da',
    'español': 'es',
    'français': 'fr',
    'norsk (bokmål)': 'nb',
    'polski': 'pl',
    'svenska': 'sv',
    'Русский': 'ru',
    'తెలుగు': 'te',
    '简体中文': 'zh-hans'
}

_config_page_title_language_map = {
    '': 'General Configuration',
    'da': 'Generel Konfiguration',
    'de': 'Allgemeine Konfiguration',
    'es': 'Configuración general',
    'fr': 'Configuration générale',
    'nb': 'Generelt oppsett',
    'nl': 'Algemene Instellingen',
    'pl': 'Ustawienia główne',
    'pt': 'Configuração Geral',
    'ru': 'Общие настройки',
    'sv': 'Allmän Konfiguration',
    'te': 'సాధారణ ఆకృతీకరణ',
    'tr': 'Genel Yapılandırma',
    'zh-hans': '常规配置',
}


@given(parsers.parse("the user {name:w} doesn't exist"))
def new_user_does_not_exist(session_browser, name):
    _delete_user(session_browser, name)


@given(parsers.parse('the user {name:w} exists'))
def test_user_exists(session_browser, name):
    functional.nav_to_module(session_browser, 'users')
    user_link = session_browser.find_link_by_href(
        '/plinth/sys/users/{}/edit/'.format(name))

    if user_link:
        _delete_user(session_browser, name)

    functional.create_user(session_browser, name, _random_string())


@given(
    parsers.parse('the admin user {name:w} with password {password:w} exists'))
def test_admin_user_exists(session_browser, name, password):
    functional.nav_to_module(session_browser, 'users')
    user_link = session_browser.find_link_by_href('/plinth/sys/users/' + name +
                                                  '/edit/')
    if user_link:
        _delete_user(session_browser, name)

    functional.create_user(session_browser, name, password, groups=['admin'])


@given(parsers.parse('the user {name:w} with password {password:w} exists'))
def user_exists(session_browser, name, password):
    functional.nav_to_module(session_browser, 'users')
    user_link = session_browser.find_link_by_href('/plinth/sys/users/' + name +
                                                  '/edit/')
    if user_link:
        _delete_user(session_browser, name)

    functional.create_user(session_browser, name, password)


@given(
    parsers.parse(
        "I'm logged in as the user {username:w} with password {password:w}"))
def logged_in_user_with_account(session_browser, username, password):
    functional.login_with_account(session_browser, functional.base_url,
                                  username, password)


@given(parsers.parse('the ssh keys are {ssh_keys:w}'))
def ssh_keys(session_browser, ssh_keys):
    _set_ssh_keys(session_browser, ssh_keys)


@given('the client has a ssh key')
def generate_ssh_keys(session_browser, tmp_path_factory):
    key_file = tmp_path_factory.getbasetemp() / 'users-ssh.key'
    try:
        key_file.unlink()
    except FileNotFoundError:
        pass

    subprocess.check_call(
        ['ssh-keygen', '-t', 'ed25519', '-N', '', '-q', '-f',
         str(key_file)])


@when(parsers.parse('I rename the user {old_name:w} to {new_name:w}'))
def rename_user(session_browser, old_name, new_name):
    _rename_user(session_browser, old_name, new_name)


@when(parsers.parse('I delete the user {name:w}'))
def delete_user(session_browser, name):
    _delete_user(session_browser, name)


@when('I change the language to <language>')
def change_language(session_browser, language):
    _set_language(session_browser, _language_codes[language])


@when(parsers.parse('I change the ssh keys to {ssh_keys:w}'))
def change_ssh_keys(session_browser, ssh_keys):
    _set_ssh_keys(session_browser, ssh_keys)


@when('I remove the ssh keys')
def remove_ssh_keys(session_browser):
    _set_ssh_keys(session_browser, '')


@when(
    parsers.parse(
        'I change the ssh keys to {ssh_keys:w} for the user {username:w}'))
def change_user_ssh_keys(session_browser, ssh_keys, username):
    _set_ssh_keys(session_browser, ssh_keys, username=username)


@when(
    parsers.parse(
        'I change my ssh keys to {ssh_keys:w} with password {password:w}'))
def change_my_ssh_keys(session_browser, ssh_keys, password):
    _set_ssh_keys(session_browser, ssh_keys, password=password)


@when(parsers.parse('I set the user {username:w} as inactive'))
def set_user_inactive(session_browser, username):
    _set_user_inactive(session_browser, username)


@when(
    parsers.parse(
        'I change my password from {current_password} to {new_password:w}'))
def change_my_password(session_browser, current_password, new_password):
    _change_password(session_browser, new_password,
                     current_password=current_password)


@when(
    parsers.parse(
        'I change the user {username:w} password to {new_password:w}'))
def change_other_user_password(session_browser, username, new_password):
    _change_password(session_browser, new_password, username=username)


@when('I configure the ssh keys')
def configure_ssh_keys(session_browser, tmp_path_factory):
    public_key_file = tmp_path_factory.getbasetemp() / 'users-ssh.key.pub'
    public_key = public_key_file.read_text()
    _set_ssh_keys(session_browser, public_key)


@then(
    parsers.parse(
        'I can log in as the user {username:w} with password {password:w}'))
def can_log_in(session_browser, username, password):
    functional.visit(session_browser, '/plinth/accounts/logout/')
    functional.login_with_account(session_browser, functional.base_url,
                                  username, password)
    assert len(session_browser.find_by_id('id_user_menu')) > 0


@then(
    parsers.parse(
        "I can't log in as the user {username:w} with password {password:w}"))
def cannot_log_in(session_browser, username, password):
    functional.visit(session_browser, '/plinth/accounts/logout/')
    functional.login_with_account(session_browser, functional.base_url,
                                  username, password)
    assert len(session_browser.find_by_id('id_user_menu')) == 0


@then('Plinth language should be <language>')
def plinth_language_should_be(session_browser, language):
    assert _check_language(session_browser, _language_codes[language])


@then(parsers.parse('the ssh keys should be {ssh_keys:w}'))
def ssh_keys_match(session_browser, ssh_keys):
    assert _get_ssh_keys(session_browser) == ssh_keys


@then('the ssh keys should be removed')
def ssh_keys_should_be_removed(session_browser, ssh_keys):
    assert _get_ssh_keys(session_browser) == ''


@then(
    parsers.parse(
        'the ssh keys should be {ssh_keys:w} for the user {username:w}'))
def ssh_keys_match_for_user(session_browser, ssh_keys, username):
    assert _get_ssh_keys(session_browser, username=username) == ssh_keys


@then(parsers.parse('my ssh keys should be {ssh_keys:w}'))
def my_ssh_keys_match(session_browser, ssh_keys):
    assert _get_ssh_keys(session_browser) == ssh_keys


@then('the client should be able to connect passwordless over ssh')
def should_connect_passwordless_over_ssh(session_browser, tmp_path_factory):
    key_file = tmp_path_factory.getbasetemp() / 'users-ssh.key'
    _try_login_to_ssh(key_file=key_file)


@then("the client shouldn't be able to connect passwordless over ssh")
def should_not_connect_passwordless_over_ssh(session_browser,
                                             tmp_path_factory):
    key_file = tmp_path_factory.getbasetemp() / 'users-ssh.key'
    with pytest.raises(subprocess.CalledProcessError):
        _try_login_to_ssh(key_file=key_file)


@then(parsers.parse('{name:w} should be listed as a user'))
def new_user_is_listed(session_browser, name):
    assert _is_user(session_browser, name)


@then(parsers.parse('{name:w} should not be listed as a user'))
def new_user_is_not_listed(session_browser, name):
    assert not _is_user(session_browser, name)


def _rename_user(browser, old_name, new_name):
    functional.nav_to_module(browser, 'users')
    with functional.wait_for_page_update(browser):
        browser.find_link_by_href('/plinth/sys/users/' + old_name +
                                  '/edit/').first.click()
    browser.find_by_id('id_username').fill(new_name)
    browser.find_by_id('id_confirm_password').fill(_admin_password)
    functional.submit(browser)


def _delete_user(browser, name):
    functional.nav_to_module(browser, 'users')
    delete_link = browser.find_link_by_href('/plinth/sys/users/' + name +
                                            '/delete/')
    if delete_link:
        with functional.wait_for_page_update(browser):
            delete_link.first.click()
        functional.submit(browser)


def _is_user(browser, name):
    functional.nav_to_module(browser, 'users')
    edit_link = browser.find_link_by_href('/plinth/sys/users/' + name +
                                          '/edit/')
    return bool(edit_link)


def _set_language(browser, language_code):
    username = functional.config['DEFAULT']['username']
    functional.visit(browser, '/plinth/sys/users/{}/edit/'.format(username))
    browser.find_by_xpath('//select[@id="id_language"]//option[@value="' +
                          language_code + '"]').first.click()
    browser.find_by_id('id_confirm_password').fill(_admin_password)
    functional.submit(browser)


def _check_language(browser, language_code):
    functional.nav_to_module(browser, 'config')
    return browser.find_by_css('.app-titles').first.find_by_tag(
        'h2').first.value == _config_page_title_language_map[language_code]


def _get_ssh_keys(browser, username=None):
    functional.visit(browser, '/plinth/')
    if username is None:
        browser.find_by_id('id_user_menu').click()
        browser.find_by_id('id_user_edit_menu').click()
    else:
        functional.visit(browser,
                         '/plinth/sys/users/{}/edit/'.format(username))
    return browser.find_by_id('id_ssh_keys').text


def _random_string(length=8):
    """Return a random string created from lower case ascii."""
    return ''.join(
        [random.choice(string.ascii_lowercase) for _ in range(length)])


def _set_ssh_keys(browser, ssh_keys, username=None, password=None):
    if username is None:
        browser.find_by_id('id_user_menu').click()
        browser.find_by_id('id_user_edit_menu').click()
    else:
        functional.visit(browser,
                         '/plinth/sys/users/{}/edit/'.format(username))

    password = password or _admin_password

    browser.find_by_id('id_ssh_keys').fill(ssh_keys)
    browser.find_by_id('id_confirm_password').fill(password)

    functional.submit(browser)


def _set_user_inactive(browser, username):
    functional.visit(browser, '/plinth/sys/users/{}/edit/'.format(username))
    browser.find_by_id('id_is_active').uncheck()
    browser.find_by_id('id_confirm_password').fill(_admin_password)
    functional.submit(browser)


def _change_password(browser, new_password, current_password=None,
                     username=None):
    current_password = current_password or _admin_password

    if username is None:
        browser.find_by_id('id_user_menu').click()
        browser.find_by_id('id_change_password_menu').click()
    else:
        functional.visit(
            browser, '/plinth/sys/users/{}/change_password/'.format(username))

    browser.find_by_id('id_new_password1').fill(new_password)
    browser.find_by_id('id_new_password2').fill(new_password)
    browser.find_by_id('id_confirm_password').fill(current_password)
    functional.submit(browser)


def _try_login_to_ssh(key_file=None):
    user = functional.config['DEFAULT']['username']
    hostname = urllib.parse.urlparse(
        functional.config['DEFAULT']['url']).hostname
    port = functional.config['DEFAULT']['ssh_port']

    subprocess.check_call([
        'ssh', '-p', port, '-i', key_file, '-q', '-o',
        'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-o',
        'BatchMode=yes', '{0}@{1}'.format(user, hostname), '/bin/true'
    ])
