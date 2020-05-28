# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for users app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

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
    user_link = session_browser.find_link_by_href('/plinth/sys/users/' + name +
                                                  '/edit/')
    if not user_link:
        create_user(session_browser, name, 'secret123')


@when(
    parsers.parse('I create a user named {name:w} with password {password:w}'))
def create_user(session_browser, name, password):
    _create_user(session_browser, name, password)


@when(parsers.parse('I rename the user {old_name:w} to {new_name:w}'))
def rename_user(session_browser, old_name, new_name):
    _rename_user(session_browser, old_name, new_name)


@when(parsers.parse('I delete the user {name:w}'))
def delete_user(session_browser, name):
    _delete_user(session_browser, name)


@then(parsers.parse('{name:w} should be listed as a user'))
def new_user_is_listed(session_browser, name):
    assert _is_user(session_browser, name)


@then(parsers.parse('{name:w} should not be listed as a user'))
def new_user_is_not_listed(session_browser, name):
    assert not _is_user(session_browser, name)


@when('I change the language to <language>')
def change_language(session_browser, language):
    _set_language(session_browser, _language_codes[language])


@then('Plinth language should be <language>')
def plinth_language_should_be(session_browser, language):
    assert _check_language(session_browser, _language_codes[language])


def _create_user(browser, name, password):
    functional.nav_to_module(browser, 'users')
    with functional.wait_for_page_update(browser):
        browser.find_link_by_href('/plinth/sys/users/create/').first.click()
    browser.find_by_id('id_username').fill(name)
    browser.find_by_id('id_password1').fill(password)
    browser.find_by_id('id_password2').fill(password)
    functional.submit(browser)


def _rename_user(browser, old_name, new_name):
    functional.nav_to_module(browser, 'users')
    with functional.wait_for_page_update(browser):
        browser.find_link_by_href('/plinth/sys/users/' + old_name +
                                  '/edit/').first.click()
    browser.find_by_id('id_username').fill(new_name)
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
    functional.submit(browser)


def _check_language(browser, language_code):
    functional.nav_to_module(browser, 'config')
    return browser.find_by_css('.app-titles').first.find_by_tag(
        'h2').first.value == _config_page_title_language_map[language_code]
