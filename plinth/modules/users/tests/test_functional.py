# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for users app.
"""

# TODO Scenario: Add user to wiki group
# TODO Scenario: Remove user from wiki group

import subprocess
import urllib

import pytest

from plinth.tests import functional

_admin_password = functional.config['DEFAULT']['password']

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.users]

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


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)
    yield
    _set_language(session_browser, _language_codes['None'])


def test_create_user(session_browser):
    """Test creating a user."""
    if functional.user_exists(session_browser, 'alice'):
        functional.delete_user(session_browser, 'alice')

    functional.create_user(session_browser, 'alice', email='alice@example.com')
    assert functional.user_exists(session_browser, 'alice')
    assert _get_email(session_browser, 'alice') == 'alice@example.com'


def test_rename_user(session_browser):
    """Test renaming a user."""
    _non_admin_user_exists(session_browser, 'alice')
    if functional.user_exists(session_browser, 'bob'):
        functional.delete_user(session_browser, 'bob')

    _rename_user(session_browser, 'alice', 'bob')
    assert not functional.user_exists(session_browser, 'alice')
    assert functional.user_exists(session_browser, 'bob')


def test_admin_users_can_change_own_ssh_keys(session_browser):
    """Test that admin users can change their own ssh keys."""
    _set_ssh_keys(session_browser, 'somekey123')
    assert _get_ssh_keys(session_browser) == 'somekey123'


def test_non_admin_users_can_change_own_ssh_keys(session_browser):
    """Test that non-admin users can change their own ssh keys."""
    _non_admin_user_exists(session_browser, 'alice')
    functional.login_with_account(session_browser, functional.base_url,
                                  'alice')
    _set_ssh_keys(session_browser, 'somekey456')
    assert _get_ssh_keys(session_browser) == 'somekey456'
    functional.login(session_browser)


def test_admin_users_can_change_other_users_ssh_keys(session_browser):
    """Test that admin users can change other user's ssh keys."""
    _non_admin_user_exists(session_browser, 'alice')
    _set_ssh_keys(session_browser, 'alicesomekey123', username='alice')
    assert _get_ssh_keys(session_browser,
                         username='alice') == 'alicesomekey123'


def test_users_can_remove_ssh_keys(session_browser):
    """Test that users can remove ssh keys."""
    _set_ssh_keys(session_browser, 'somekey123')
    _set_ssh_keys(session_browser, '')
    assert _get_ssh_keys(session_browser) == ''


def test_users_can_connect_passwordless_over_ssh(session_browser,
                                                 tmp_path_factory):
    """Test that users can connect passwordless over ssh if the keys are
    set."""
    functional.app_enable(session_browser, 'ssh')
    _configure_ssh_keys(session_browser, tmp_path_factory)
    _should_connect_passwordless_over_ssh(session_browser, tmp_path_factory)


def test_users_cannot_connect_passwordless_over_ssh(session_browser,
                                                    tmp_path_factory):
    """Test that users cannot connect passwordless over ssh if the keys aren't
    set."""
    functional.app_enable(session_browser, 'ssh')
    _configure_ssh_keys(session_browser, tmp_path_factory)
    _set_ssh_keys(session_browser, '')
    _should_not_connect_passwordless_over_ssh(session_browser,
                                              tmp_path_factory)


def test_update_user(session_browser):
    """Test changing properties of a user."""
    functional.create_user(session_browser, 'alice', email='alice@example.com')

    # Update email
    _set_email(session_browser, 'alice', 'alice1@example.com')
    assert _get_email(session_browser, 'alice') == 'alice1@example.com'
    _set_email(session_browser, 'alice', 'alice2@example.com')
    assert _get_email(session_browser, 'alice') == 'alice2@example.com'


@pytest.mark.parametrize('language_code', _language_codes.values())
def test_change_language(session_browser, language_code):
    """Test changing the language."""
    _set_language(session_browser, language_code)
    assert _check_language(session_browser, language_code)


def test_user_states(session_browser, tmp_path_factory):
    """Test that admin users can set other users as inactive/active."""
    username = 'bob2'
    _non_admin_user_exists(session_browser, username,
                           groups=["freedombox-ssh"])
    _configure_ssh_keys(session_browser, tmp_path_factory, username=username)

    # Test set user inactive
    _set_user_status(session_browser, username, 'inactive')
    # Test Django login
    _cannot_log_in(session_browser, username)
    # Test PAM/nslcd authorization
    _should_not_connect_passwordless_over_ssh(session_browser,
                                              tmp_path_factory,
                                              username=username)

    # Test set user active
    functional.login(session_browser)
    _set_user_status(session_browser, username, 'active')
    _can_log_in(session_browser, username)
    _should_connect_passwordless_over_ssh(session_browser, tmp_path_factory,
                                          username=username)

    functional.login(session_browser)


def test_admin_users_can_change_own_password(session_browser):
    """Test that admin users can change their own password."""
    _admin_user_exists(session_browser, 'testadmin')
    functional.login_with_account(session_browser, functional.base_url,
                                  'testadmin')
    _change_password(session_browser, 'newpassword456')
    _can_log_in_with_password(session_browser, 'testadmin', 'newpassword456')
    functional.login(session_browser)


def test_admin_users_can_change_others_password(session_browser):
    """Test that admin users can change other user's password."""
    _non_admin_user_exists(session_browser, 'alice')
    _change_password(session_browser, 'secretsecret567', username='alice')
    _can_log_in_with_password(session_browser, 'alice', 'secretsecret567')
    functional.login(session_browser)


def test_non_admin_users_can_change_own_password(session_browser):
    """Test that non-admin users can change their own password."""
    _non_admin_user_exists(session_browser, 'alice')
    functional.login_with_account(session_browser, functional.base_url,
                                  'alice')
    _change_password(session_browser, 'newpassword123')
    _can_log_in_with_password(session_browser, 'alice', 'newpassword123')
    functional.login(session_browser)


def test_delete_user(session_browser):
    """Test deleting a user."""
    _non_admin_user_exists(session_browser, 'alice')
    functional.delete_user(session_browser, 'alice')
    assert not functional.user_exists(session_browser, 'alice')


def _admin_user_exists(session_browser, name):
    if functional.user_exists(session_browser, name):
        functional.delete_user(session_browser, name)
    functional.create_user(session_browser, name, groups=['admin'])


def _non_admin_user_exists(session_browser, name, groups=[]):
    if functional.user_exists(session_browser, name):
        functional.delete_user(session_browser, name)
    functional.create_user(session_browser, name, groups=groups)


def _generate_ssh_keys(session_browser, key_file):
    try:
        key_file.unlink()
    except FileNotFoundError:
        pass

    subprocess.check_call(
        ['ssh-keygen', '-t', 'ed25519', '-N', '', '-q', '-f',
         str(key_file)])


def _configure_ssh_keys(session_browser, tmp_path_factory, username=None):
    key_file = tmp_path_factory.getbasetemp() / 'users-ssh.key'
    _generate_ssh_keys(session_browser, key_file)
    public_key_file = key_file.with_suffix(key_file.suffix + '.pub')
    public_key = public_key_file.read_text()
    _set_ssh_keys(session_browser, public_key, username=username)


def _can_log_in(session_browser, username):
    functional.login_with_account(session_browser, functional.base_url,
                                  username)
    assert len(session_browser.find_by_id('id_user_menu')) > 0


def _can_log_in_with_password(session_browser, username, password):
    functional.logout(session_browser)
    functional.login_with_account(session_browser, functional.base_url,
                                  username, password)
    assert len(session_browser.find_by_id('id_user_menu')) > 0


def _cannot_log_in(session_browser, username):
    functional.login_with_account(session_browser, functional.base_url,
                                  username)
    assert len(session_browser.find_by_id('id_user_menu')) == 0


def _should_connect_passwordless_over_ssh(session_browser, tmp_path_factory,
                                          username=None):
    key_file = tmp_path_factory.getbasetemp() / 'users-ssh.key'
    _try_login_to_ssh(key_file=key_file, username=username)


def _should_not_connect_passwordless_over_ssh(session_browser,
                                              tmp_path_factory, username=None):
    key_file = tmp_path_factory.getbasetemp() / 'users-ssh.key'
    with pytest.raises(subprocess.CalledProcessError):
        _try_login_to_ssh(key_file=key_file, username=username)


def _rename_user(browser, old_name, new_name):
    functional.nav_to_module(browser, 'users')
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href('/plinth/sys/users/' + old_name +
                                   '/edit/').first.click()
    browser.find_by_id('id_username').fill(new_name)
    browser.find_by_id('id_confirm_password').fill(_admin_password)
    functional.submit(browser, form_class='form-update')


def _set_email(browser, username, email):
    """Set the email field value for a user."""
    functional.visit(browser, '/plinth/sys/users/{}/edit/'.format(username))
    browser.find_by_id('id_email').fill(email)
    browser.find_by_id('id_confirm_password').fill(_admin_password)
    functional.submit(browser, form_class='form-update')


def _get_email(browser, username):
    """Return the email field value for a user."""
    functional.visit(browser, '/plinth/sys/users/{}/edit/'.format(username))
    return browser.find_by_id('id_email').value


def _set_language(browser, language_code):
    username = functional.config['DEFAULT']['username']
    functional.visit(browser, '/plinth/sys/users/{}/edit/'.format(username))
    browser.find_by_xpath('//select[@id="id_language"]//option[@value="' +
                          language_code + '"]').first.click()
    browser.find_by_id('id_confirm_password').fill(_admin_password)
    functional.submit(browser, form_class='form-update')


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


def _set_ssh_keys(browser, ssh_keys, username=None):
    if username is None:
        browser.find_by_id('id_user_menu').click()
        browser.find_by_id('id_user_edit_menu').click()
    else:
        functional.visit(browser,
                         '/plinth/sys/users/{}/edit/'.format(username))

    current_user = browser.find_by_id('id_user_menu_link').text
    auth_password = functional.get_password(current_user)

    browser.find_by_id('id_ssh_keys').fill(ssh_keys)
    browser.find_by_id('id_confirm_password').fill(auth_password)

    functional.submit(browser, form_class='form-update')


def _set_user_status(browser, username, status):
    functional.visit(browser, '/plinth/sys/users/{}/edit/'.format(username))
    if status == "inactive":
        browser.find_by_id('id_is_active').uncheck()
    elif status == "active":
        browser.find_by_id('id_is_active').check()
    browser.find_by_id('id_confirm_password').fill(_admin_password)
    functional.submit(browser, form_class='form-update')


def _change_password(browser, new_password, current_password=None,
                     username=None):
    if username is None:
        browser.find_by_id('id_user_menu').click()
        browser.find_by_id('id_change_password_menu').click()
    else:
        functional.visit(
            browser, '/plinth/sys/users/{}/change_password/'.format(username))

    current_user = browser.find_by_id('id_user_menu_link').text
    auth_password = current_password or functional.get_password(current_user)

    browser.find_by_id('id_new_password1').fill(new_password)
    browser.find_by_id('id_new_password2').fill(new_password)
    browser.find_by_id('id_confirm_password').fill(auth_password)
    functional.submit(browser, form_class='form-change-password')


def _try_login_to_ssh(key_file=None, username=None):
    user = username if username else functional.config['DEFAULT']['username']
    hostname = urllib.parse.urlparse(
        functional.config['DEFAULT']['url']).hostname
    port = functional.config['DEFAULT']['ssh_port']

    subprocess.check_call([
        'ssh', '-p', port, '-i', key_file, '-q', '-o',
        'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-o',
        'BatchMode=yes', '{0}@{1}'.format(user, hostname), '/bin/true'
    ])
