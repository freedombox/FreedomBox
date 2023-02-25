# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for dynamicdns app.
"""

import pytest

from plinth.tests import functional

pytestmark = [
    pytest.mark.system, pytest.mark.essential, pytest.mark.domain,
    pytest.mark.dynamicdns
]

_configs = {
    'gnudip1': {
        'service_type': 'gnudip',
        'server': 'localhost',
        'domain': 'freedombox.example.com',
        'username': 'tester',
        'password': 'testingtesting',
        'ip_lookup_url': 'https://ddns.freedombox.org/ip/',
    },
    'gnudip2': {
        'service_type': 'gnudip',
        'server': '127.0.0.1',
        'domain': 'freedombox2.example.com',
        'username': 'tester2',
        'password': 'testingtesting2',
        'ip_lookup_url': 'https://ddns2.freedombox.org/ip/',
    },
    'noip.com': {
        'service_type': 'noip.com',
        'update_url': 'https://localhost/update3/',
        'disable_ssl_cert_check': True,
        'use_http_basic_auth': True,
        'domain': 'freedombox3.example.com',
        'username': 'tester3',
        'password': 'testingtesting3',
        'ip_lookup_url': 'https://ddns3.freedombox.org/ip/',
        'use_ipv6': True,
    },
    'freedns.afraid.org': {
        'service_type': 'freedns.afraid.org',
        'update_url': 'https://localhost/update5/',
        'disable_ssl_cert_check': False,
        'use_http_basic_auth': False,
        'domain': 'freedombox5.example.com',
        'username': '',
        'password': '',
        'ip_lookup_url': '',
        'use_ipv6': False,
    },
    'other': {
        'service_type': 'other',
        'update_url': 'https://localhost/update6/',
        'disable_ssl_cert_check': False,
        'use_http_basic_auth': False,
        'domain': 'freedombox6.example.com',
        'username': 'tester6',
        'password': 'testingtesting6',
        'ip_lookup_url': 'https://ddns6.freedombox.org/ip/',
        'use_ipv6': False,
    },
}


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


class TestDynamicDNSApp(functional.BaseAppTests):
    app_name = 'dynamicdns'
    has_service = False
    has_web = False
    can_uninstall = False
    check_diagnostics = False

    @staticmethod
    def test_capitalized_domain_name(session_browser):
        """Test handling of capitalized domain name."""
        _configure(session_browser, _configs['gnudip1'])
        _configure(session_browser, {'domain': 'FreedomBox.example.com'})
        _assert_has_config(session_browser,
                           {'domain': 'freedombox.example.com'})

    @staticmethod
    @pytest.mark.parametrize('config_name', list(_configs.keys()))
    def test_various_form_values(session_browser, config_name):
        """Test feeding various values and check that they are saved."""
        _configure(session_browser, _configs[config_name])
        _assert_has_config(session_browser, _configs[config_name])

    @staticmethod
    @pytest.mark.backups
    def test_backup_restore(session_browser):
        """Test backup and restore of configuration."""
        _configure(session_browser, _configs['gnudip1'])
        functional.backup_create(session_browser, 'dynamicdns',
                                 'test_dynamicdns')

        _configure(session_browser, _configs['gnudip2'])
        functional.backup_restore(session_browser, 'dynamicdns',
                                  'test_dynamicdns')

        _assert_has_config(session_browser, _configs['gnudip1'])


def _configure(browser, config):
    functional.nav_to_module(browser, 'dynamicdns')
    for key, value in config.items():
        if key == 'service_type':
            browser.find_by_id(f'id_{key}').select(value)
        elif isinstance(value, bool):
            if value:
                browser.find_by_id(f'id_{key}').check()
            else:
                browser.find_by_id(f'id_{key}').uncheck()
        else:
            browser.find_by_id(f'id_{key}').fill(value)

    functional.submit(browser, form_class='form-configuration')


def _assert_has_config(browser, config):
    functional.nav_to_module(browser, 'dynamicdns')
    for key, value in config.items():
        if key == 'password':
            continue

        if isinstance(value, bool):
            assert browser.find_by_id(f'id_{key}').checked == value
        else:
            assert value == browser.find_by_id(f'id_{key}').value


def _get_domain(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    return browser.find_by_id('id_domain').value
