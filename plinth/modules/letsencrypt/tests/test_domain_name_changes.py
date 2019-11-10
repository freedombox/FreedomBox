#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
        certificate_revoke.assert_has_calls([call(domain)])
    else:
        certificate_revoke.assert_not_called()
