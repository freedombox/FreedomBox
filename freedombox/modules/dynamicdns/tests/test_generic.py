# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for generic URL based Dynamic DNS updates.
"""

import subprocess
from unittest.mock import call, patch

import pytest

from .. import generic


@pytest.fixture(name='domain')
def fixture_domain():
    """Return a domain configuration."""
    return {
        'domain': 'example.org',
        'update_url': ('https://<User>:<Pass>@example.com'
                       '/update?hostname=<Domain>&ip=<Ip>'),
        'username': 'tester',
        'password': 'testingtesting',
        'use_http_basic_auth': False,
        'disable_ssl_cert_check': True,
    }


@patch('subprocess.run')
def test_update_ip_types(run, domain):
    """Test that various IP types are handled as expected."""
    # IPv4
    generic.update(domain, 'ipv4', external_address='1.1.1.1')
    assert '-4' in run.mock_calls[0].args[0]

    # IPv6
    run.reset_mock()
    generic.update(domain, 'ipv6', external_address='1.1.1.1')
    assert '-6' in run.mock_calls[0].args[0]


@patch('subprocess.run')
def test_update_ssl_cert_check(run, domain):
    """Test that SSL certificate check can be disabled."""
    # Check certificate
    generic.update(domain, 'ipv4', external_address='1.1.1.1')
    assert '--no-check-certificate' in run.mock_calls[0].args[0]

    # Don't check certificate
    run.reset_mock()
    domain['disable_ssl_cert_check'] = False
    generic.update(domain, 'ipv4', external_address='1.1.1.1')
    assert '--no-check-certificate' not in run.mock_calls[0].args[0]


@patch('subprocess.run')
def test_update_basic_auth(run, domain):
    """Test that using basic authentication works."""
    # Check certificate
    generic.update(domain, 'ipv4', external_address='1.1.1.1')
    assert '--username' not in run.mock_calls[0].args[0]
    assert '--password' not in run.mock_calls[0].args[0]

    # Don't check certificate
    run.reset_mock()
    domain['use_http_basic_auth'] = True
    generic.update(domain, 'ipv4', external_address='1.1.1.1')
    assert ['--user', 'tester', '--password',
            'testingtesting'] == run.mock_calls[0].args[0][7:11]


@patch('subprocess.run')
def test_update_url_parameters(run, domain):
    """Test that replacing parameters in the URL works as expected."""
    generic.update(domain, 'ipv4', external_address='1.1.1.1')
    expected_url = ('https://tester:testingtesting@example.com/update?'
                    'hostname=example.org&ip=1.1.1.1')
    assert expected_url in run.mock_calls[0].args[0]

    # No substitution for unavailable values
    run.reset_mock()
    generic.update(domain, 'ipv4', external_address=None)
    expected_url = ('https://tester:testingtesting@example.com/update?'
                    'hostname=example.org&ip=<Ip>')
    assert expected_url in run.mock_calls[0].args[0]


@patch('subprocess.run')
def test_update_call(run, domain):
    """Test that calling the wget command is as expected."""
    generic.update(domain, 'ipv4', external_address='1.1.1.1')
    assert run.mock_calls == [
        call([
            'wget', '-O', '-', '-t', '3', '-T', '3', '--no-check-certificate',
            '-4',
            ('https://tester:testingtesting@example.com/update?'
             'hostname=example.org&ip=1.1.1.1')
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ]


@patch('subprocess.run')
def test_update_return_value(run, domain):
    """Test that return value or raising exception works."""
    assert '1.1.1.1' == generic.update(domain, 'ipv4',
                                       external_address='1.1.1.1')

    run.side_effect = subprocess.CalledProcessError(1, ['foo'])
    with pytest.raises(subprocess.CalledProcessError) as exception_info:
        generic.update(domain, 'ipv4', external_address='1.1.1.1')

    assert exception_info.value.returncode == 1
    assert exception_info.value.cmd == ['foo']
