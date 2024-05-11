# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for webserver components.
"""

import subprocess
from unittest.mock import call, patch

import pytest

from plinth import app
from plinth.diagnostic_check import DiagnosticCheck, Result
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


@patch('plinth.modules.apache.privileged.enable')
def test_webserver_enable(enable):
    """Test that enabling webserver configuration works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver.enable()
    enable.assert_has_calls([call('test-config', 'module')])


@patch('plinth.modules.apache.privileged.disable')
def test_webserver_disable(disable):
    """Test that disabling webserver configuration works."""
    webserver = Webserver('test-webserver', 'test-config', kind='module')

    webserver.disable()
    disable.assert_has_calls([call('test-config', 'module')])


@patch('plinth.modules.apache.components.diagnose_url')
@patch('plinth.modules.apache.components.diagnose_url_on_all')
def test_webserver_diagnose(diagnose_url_on_all, diagnose_url):
    """Test running diagnostics."""

    def on_all_side_effect(url, check_certificate, expect_redirects,
                           component_id):
        return [
            DiagnosticCheck('test-all-id', 'test-result-' + url, 'success', {},
                            component_id)
        ]

    def side_effect(url, check_certificate, component_id):
        return DiagnosticCheck('test-id', 'test-result-' + url, 'success', {},
                               component_id)

    diagnose_url_on_all.side_effect = on_all_side_effect
    diagnose_url.side_effect = side_effect
    webserver1 = Webserver('test-webserver', 'test-config',
                           urls=['{host}url1', 'url2'], expect_redirects=True)
    results = webserver1.diagnose()
    assert results == [
        DiagnosticCheck('test-all-id', 'test-result-{host}url1', 'success', {},
                        'test-webserver'),
        DiagnosticCheck('test-id', 'test-result-url2', 'success', {},
                        'test-webserver')
    ]
    diagnose_url_on_all.assert_has_calls([
        call('{host}url1', check_certificate=False, expect_redirects=True,
             component_id='test-webserver')
    ])
    diagnose_url.assert_has_calls(
        [call('url2', check_certificate=False, component_id='test-webserver')])

    diagnose_url_on_all.reset_mock()
    webserver2 = Webserver('test-webserver', 'test-config',
                           urls=['{host}url1', 'url2'], expect_redirects=False)
    results = webserver2.diagnose()
    diagnose_url_on_all.assert_has_calls([
        call('{host}url1', check_certificate=False, expect_redirects=False,
             component_id='test-webserver')
    ])


@patch('plinth.privileged.service.restart')
@patch('plinth.privileged.service.reload')
def test_webserver_setup(service_reload, service_restart):
    """Test that component restart/reloads web server during app upgrades."""

    class AppTest(app.App):
        app_id = 'testapp'
        enabled = False

        def is_enabled(self):
            return self.enabled

    app1 = AppTest()

    # Don't fail when last_updated_version is not provided.
    webserver1 = Webserver('test-webserver1', 'test-config')
    assert webserver1.last_updated_version == 0
    webserver1.setup(old_version=10)
    service_reload.assert_not_called()
    service_restart.assert_not_called()

    webserver1 = Webserver('test-webserver1', 'test-config',
                           last_updated_version=5)
    for version in (0, 5, 6):
        webserver1.setup(old_version=version)
        service_reload.assert_not_called()
        service_restart.assert_not_called()

    app1.enabled = False
    webserver2 = Webserver('test-webserver2', 'test-config',
                           last_updated_version=5)
    app1.add(webserver2)
    webserver2.setup(old_version=3)
    service_reload.assert_not_called()
    service_restart.assert_not_called()

    app1.enabled = True
    webserver3 = Webserver('test-webserver3', 'test-config',
                           last_updated_version=5)
    app1.add(webserver3)
    webserver3.setup(old_version=3)
    service_reload.assert_has_calls([call('apache2')])
    service_restart.assert_not_called()
    service_reload.reset_mock()

    webserver4 = Webserver('test-webserver', 'test-module', 'module',
                           last_updated_version=5)
    app1.add(webserver4)
    webserver4.setup(old_version=3)
    service_restart.assert_has_calls([call('apache2')])
    service_reload.assert_not_called()


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


@patch('plinth.modules.apache.privileged.uwsgi_enable')
def test_uwsgi_enable(enable):
    """Test that enabling uwsgi configuration works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi.enable()
    enable.assert_has_calls([call('test-config')])


@patch('plinth.modules.apache.privileged.uwsgi_disable')
def test_uwsgi_disable(disable):
    """Test that disabling uwsgi configuration works."""
    uwsgi = Uwsgi('test-uwsgi', 'test-config')

    uwsgi.disable()
    disable.assert_has_calls([call('test-config')])


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
        'expected_output': 'test-expected',
        'component_id': 'test-component',
    }
    parameters = {key: args[key] for key in ['url', 'kind']}
    check.return_value = True
    result = diagnose_url(**args)
    assert result == DiagnosticCheck(
        'apache-url-kind-https://localhost/test-4',
        'Access URL {url} on tcp{kind}', Result.PASSED, parameters,
        'test-component')

    check.return_value = False
    result = diagnose_url(**args)
    assert result == DiagnosticCheck(
        'apache-url-kind-https://localhost/test-4',
        'Access URL {url} on tcp{kind}', Result.FAILED, parameters,
        'test-component')

    del args['kind']
    args['url'] = 'https://{host}/test'
    check.return_value = True
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
    parameters = [
        {
            'url': 'https://test-host-1/test',
            'kind': '4'
        },
        {
            'url': 'https://test-host-2/test',
            'kind': '6'
        },
    ]
    results = diagnose_url_on_all(**args)
    assert results == [
        DiagnosticCheck('apache-url-kind-https://test-host-1/test-4',
                        'Access URL {url} on tcp{kind}', Result.PASSED,
                        parameters[0], 'test-component'),
        DiagnosticCheck('apache-url-kind-https://test-host-2/test-6',
                        'Access URL {url} on tcp{kind}', Result.PASSED,
                        parameters[1], 'test-component'),
    ]


@patch('subprocess.run')
def test_check_url(run):
    """Test checking whether a URL is accessible."""
    url = 'http://localhost/test'
    basic_command = ['curl', '--location', '-f', '-w', '%{response_code}']
    extra_args = {'env': None, 'check': True, 'stdout': -1, 'stderr': -1}

    # Basic
    assert check_url(url)
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
    assert not check_url(url)

    # Return code 401, 405
    run.side_effect = exception
    run.side_effect.stdout = b' 401 '
    assert check_url(url)
    run.side_effect.stdout = b'405\n'
    assert check_url(url)

    # Error
    run.side_effect = FileNotFoundError()
    with pytest.raises(FileNotFoundError):
        assert check_url(url)
