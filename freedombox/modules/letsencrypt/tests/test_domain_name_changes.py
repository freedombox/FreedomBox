# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for letsencrypt module.
"""

from unittest.mock import call, patch

import pytest

from plinth.modules.names.components import DomainType

from .. import on_domain_added, on_domain_removed


@pytest.fixture(name='domain_types')
def fixture_domain_types():
    """Create a domain types required for tests."""
    DomainType('domain-type-tor', 'Tor Onion Service', 'tor:index',
               can_have_certificate=False)
    DomainType('domain-type-test', 'Test Domain Type', 'test:index')


@pytest.mark.usefixtures('domain_types')
def test_add_onion_domain():
    """Test that .onion domains are ignored when added/removed."""
    assert not on_domain_added('test', 'domain-type-tor', 'ddddd.onion')
    assert not on_domain_removed('test', 'domain-type-tor', 'ddddd.onion')


@patch('plinth.modules.letsencrypt.get_status')
@patch('plinth.modules.letsencrypt.certificate_obtain')
@pytest.mark.usefixtures('load_cfg')
@pytest.mark.parametrize('domain,status_input,obtain,result', [
    ('domain1.tld', {
        'certificate_available': True,
        'validity': 'not-valid'
    }, True, True),
    ('domain2.tld', {
        'certificate_available': False,
        'validity': 'valid'
    }, True, True),
    ('domain3.tld', {
        'certificate_available': True,
        'validity': 'valid'
    }, False, False),
    ('', {
        'certificate_available': False,
        'validity': 'valid'
    }, False, True),
])
def test_add_valid_domain(certificate_obtain, get_status, domain, status_input,
                          obtain, result):
    """Test adding a domain that can have certificates."""
    get_status.return_value = {'domains': {domain: status_input}}
    assert result == on_domain_added('test', 'domain-type-test', domain)
    if obtain:
        certificate_obtain.assert_has_calls([call(domain)])
    else:
        certificate_obtain.assert_not_called()


@patch('plinth.modules.letsencrypt.certificate_revoke')
@pytest.mark.usefixtures('load_cfg')
@pytest.mark.parametrize('domain,revoke,result', [
    ('domain1.tld', True, True),
    ('', False, True),
])
def test_remove_domain(certificate_revoke, domain, revoke, result):
    """Test removing a domain that can certificates."""
    assert result == on_domain_removed('test', 'domain-type-test', domain)
    if revoke:
        certificate_revoke.assert_has_calls(
            [call(domain, really_revoke=False)])
    else:
        certificate_revoke.assert_not_called()
