# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for webserver components.
"""

import subprocess
from unittest.mock import call, patch

import pytest

from plinth.modules.apache.components import (Uwsgi, Webserver, check_url,
                                              diagnose_url,
                                              diagnose_url_on_all)


def test_webserver_init():
    """Test that webserver component can be initialized."""
    with pytest.raises(ValueError):
        Webserver(None, None)

    webserver = Webserver('test-webserver', 'test-config', kind='module',
                          urls=['url1', 'url2'], expect_redirects=True)
    assert webserver.component_id == 'test-webserver'
    assert webserver.web_name == 'test-config'
    assert webserver.kind == 'module'
    assert webserver.urls == ['url1', 'url2']
    assert webserver.expect_redirects

    webserver = Webserver('test-webserver', None)
    assert webserver.kind == 'config'
    assert webserver.urls == []
    assert not webserver.expect_redirects


@patch('plinth.action_utils.webserver_is_enabled')
def test_webserver_is_enabled(webserver_is_enabled):
    """Test that checking webserver configuration enabled works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver_is_enabled.return_value = True
    assert webserver.is_enabled()
    webserver_is_enabled.assert_has_calls([call('test-config', kind='module')])

    webserver_is_enabled.reset_mock()
    webserver_is_enabled.return_value = False
    assert not webserver.is_enabled()
    webserver_is_enabled.assert_has_calls([call('test-config', kind='module')])


@patch('plinth.actions.superuser_run')
def test_webserver_enable(superuser_run):
    """Test that enabling webserver configuration works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver.enable()
    superuser_run.assert_has_calls([
        call('apache', ['enable', '--name', 'test-config', '--kind', 'module'])
    ])


@patch('plinth.actions.superuser_run')
def test_webserver_disable(superuser_run):
    """Test that disabling webserver configuration works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver.disable()
    superuser_run.assert_has_calls([
        call('apache',
             ['disable', '--name', 'test-config', '--kind', 'module'])
    ])


@patch('plinth.modules.apache.components.diagnose_url')
@patch('plinth.modules.apache.components.diagnose_url_on_all')
def test_webserver_diagnose(diagnose_url_on_all, diagnose_url):
    """Test running diagnostics."""

    def on_all_side_effect(url, check_certificate, expect_redirects):
        return [('test-result-' + url, 'success')]

    def side_effect(url, check_certificate):
        return ('test-result-' + url, 'success')

    diagnose_url_on_all.side_effect = on_all_side_effect
    diagnose_url.side_effect = side_effect
    webserver1 = Webserver('test-webserver', 'test-config',
                           urls=['{host}url1', 'url2'], expect_redirects=True)
    results = webserver1.diagnose()
    assert results == [('test-result-{host}url1', 'success'),
                       ('test-result-url2', 'success')]
    diagnose_url_on_all.assert_has_calls(
        [call('{host}url1', check_certificate=False, expect_redirects=True)])
    diagnose_url.assert_has_calls([call('url2', check_certificate=False)])

    diagnose_url_on_all.reset_mock()
    webserver2 = Webserver('test-webserver', 'test-config',
                           urls=['{host}url1', 'url2'], expect_redirects=False)
    results = webserver2.diagnose()
    diagnose_url_on_all.assert_has_calls(
        [call('{host}url1', check_certificate=False, expect_redirects=False)])


def test_uwsgi_init():
    """Test that uWSGI component can be initialized."""
    with pytest.raises(ValueError):
        Uwsgi(None, None)

    uwsgi = Uwsgi('test-uwsgi', 'test-config')
    assert uwsgi.component_id == 'test-uwsgi'
    assert uwsgi.uwsgi_name == 'test-config'


@patch('plinth.action_utils.service_is_enabled')
@patch('plinth.action_utils.uwsgi_is_enabled')
def test_uwsgi_is_enabled(uwsgi_is_enabled, service_is_enabled):
    """Test that checking uwsgi configuration enabled works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi_is_enabled.return_value = True
    service_is_enabled.return_value = True
    assert uwsgi.is_enabled()
    uwsgi_is_enabled.assert_has_calls([call('test-config')])
    service_is_enabled.assert_has_calls([call('uwsgi')])

    service_is_enabled.return_value = False
    assert not uwsgi.is_enabled()

    uwsgi_is_enabled.return_value = False
    assert not uwsgi.is_enabled()

    service_is_enabled.return_value = False
    assert not uwsgi.is_enabled()


@patch('plinth.actions.superuser_run')
def test_uwsgi_enable(superuser_run):
    """Test that enabling uwsgi configuration works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi.enable()
    superuser_run.assert_has_calls(
        [call('apache', ['uwsgi-enable', '--name', 'test-config'])])


@patch('plinth.actions.superuser_run')
def test_uwsgi_disable(superuser_run):
    """Test that disabling uwsgi configuration works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi.disable()
    superuser_run.assert_has_calls(
        [call('apache', ['uwsgi-disable', '--name', 'test-config'])])


@patch('plinth.action_utils.service_is_running')
@patch('plinth.action_utils.uwsgi_is_enabled')
def test_uwsgi_is_running(uwsgi_is_enabled, service_is_running):
    """Test checking whether uwsgi is running with a configuration."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi_is_enabled.return_value = True
    service_is_running.return_value = True
    assert uwsgi.is_running()
    uwsgi_is_enabled.assert_has_calls([call('test-config')])
    service_is_running.assert_has_calls([call('uwsgi')])

    uwsgi_is_enabled.return_value = False
    service_is_running.return_value = True
    assert not uwsgi.is_running()

    uwsgi_is_enabled.return_value = True
    service_is_running.return_value = False
    assert not uwsgi.is_running()

    uwsgi_is_enabled.return_value = False
    service_is_running.return_value = False
    assert not uwsgi.is_running()


@patch('plinth.modules.apache.components.check_url')
@patch('plinth.action_utils.get_addresses')
def test_diagnose_url(get_addresses, check):
    """Test diagnosing a URL."""
    args = {
        'url': 'https://localhost/test',
        'kind': '4',
        'env': {
            'test': 'value'
        },
        'check_certificate': False,
        'extra_options': {
            'test-1': 'value-1'
        },
        'wrapper': 'test-wrapper',
        'expected_output': 'test-expected'
    }
    check.return_value = 'passed'
    result = diagnose_url(**args)
    assert result == ['Access URL https://localhost/test on tcp4', 'passed']

    check.return_value = 'failed'
    result = diagnose_url(**args)
    assert result == ['Access URL https://localhost/test on tcp4', 'failed']

    del args['kind']
    args['url'] = 'https://{host}/test'
    check.return_value = 'passed'
    get_addresses.return_value = [{
        'kind': '4',
        'address': 'test-host-1',
        'numeric': False,
        'url_address': 'test-host-1'
    }, {
        'kind': '6',
        'address': 'test-host-2',
        'numeric': False,
        'url_address': 'test-host-2'
    }]
    result = diagnose_url_on_all(**args)
    assert result == [
        ['Access URL https://test-host-1/test on tcp4', 'passed'],
        ['Access URL https://test-host-2/test on tcp6', 'passed'],
    ]


@patch('subprocess.run')
def test_check_url(run):
    """Test checking whether a URL is accessible."""
    url = 'http://localhost/test'
    basic_command = ['curl', '--location', '-f', '-w', '%{response_code}']
    extra_args = {'env': None, 'check': True, 'stdout': -1, 'stderr': -1}

    # Basic
    assert check_url(url) == 'passed'
    run.assert_called_with(basic_command + [url], **extra_args)

    # Wrapper
    check_url(url, wrapper='test-wrapper')
    run.assert_called_with(['test-wrapper'] + basic_command + [url],
                           **extra_args)

    # No certificate check
    check_url(url, check_certificate=False)
    run.assert_called_with(basic_command + [url, '-k'], **extra_args)

    # Extra options
    check_url(url, extra_options=['test-opt1', 'test-opt2'])
    run.assert_called_with(basic_command + [url, 'test-opt1', 'test-opt2'],
                           **extra_args)

    # TCP4/TCP6
    check_url(url, kind='4')
    run.assert_called_with(basic_command + [url, '-4'], **extra_args)
    check_url(url, kind='6')
    run.assert_called_with(basic_command + [url, '-6'], **extra_args)

    # IPv6 Link Local URLs
    check_url('https://[::2%eth0]/test', kind='6')
    run.assert_called_with(
        basic_command + ['--interface', 'eth0', 'https://[::2]/test', '-6'],
        **extra_args)

    # Failure
    exception = subprocess.CalledProcessError(returncode=1, cmd=['curl'])
    run.side_effect = exception
    run.side_effect.stdout = b'500'
    assert check_url(url) == 'failed'

    # Return code 401, 405
    run.side_effect = exception
    run.side_effect.stdout = b' 401 '
    assert check_url(url) == 'passed'
    run.side_effect.stdout = b'405\n'
    assert check_url(url) == 'passed'

    # Error
    run.side_effect = FileNotFoundError()
    assert check_url(url) == 'error'
