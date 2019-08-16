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
Test the App components provides by names app.
"""

import pytest

from ..components import DomainName, DomainType


@pytest.fixture(name='domain_type')
def fixture_domain_type():
    """Fixture to create a domain type after clearing all existing ones."""
    DomainType._all = {}
    return DomainType('test-domain-type', 'x-display-name', 'config_url')


@pytest.fixture(name='domain_name')
def fixture_domain_name(domain_type):
    DomainName._all = {}
    return DomainName('test-domain-name', 'test.example.com',
                      'test-domain-type', ['http', 443, 'ssh', 9000])


def test_domain_type_init():
    """Test initialization of domain type object."""
    component = DomainType('test-component', 'x-display-name', 'config_url')
    assert component.component_id == 'test-component'
    assert component.display_name == 'x-display-name'
    assert component.configuration_url == 'config_url'
    assert component.can_have_certificate
    assert len(DomainType._all)
    assert DomainType._all['test-component'] == component

    component = DomainType('test-component', 'x-display-name', 'config_url',
                           can_have_certificate=False)
    assert not component.can_have_certificate


def test_domain_type_get(domain_type):
    """Test getting domain type object."""
    assert DomainType.get('test-domain-type') == domain_type
    with pytest.raises(KeyError):
        DomainType.get('unknown-domain-type')


def test_domain_type_list(domain_type):
    """Test listing of all domain types."""
    assert DomainType.list()['test-domain-type'] == domain_type
    assert id(DomainType.list()) != id(DomainType._all)


def test_domain_name_init(domain_type):
    """Test initializing a domain name."""
    component = DomainName('test-component', 'test.example.com',
                           'test-domain-type', '__all__')

    assert component.component_id == 'test-component'
    assert component.name == 'test.example.com'
    assert component.domain_type == domain_type
    assert component.services == '__all__'
    assert len(DomainName._all)
    assert DomainName._all['test-component'] == component


def test_domain_name_service_normalization(domain_name):
    """Test that passed services get normalized during initialization."""
    assert set(domain_name.services) == {'http', 'https', 'ssh', '9000'}


def test_domain_name_getting_readable_services(domain_name):
    """Test that getting readable string for services works"""
    strings = [str(string) for string in domain_name.get_readable_services()]
    assert sorted(strings) == sorted(['All web apps', 'Secure Shell', '9000'])


def test_domain_name_has_service(domain_name):
    """Test checking if a domain name provides a service."""
    assert domain_name.has_service('http')
    assert domain_name.has_service('https')
    assert domain_name.has_service('9000')
    assert not domain_name.has_service('1234')
    assert domain_name.has_service(None)

    domain_name._services = '__all__'
    assert domain_name.has_service('1234')


def test_domain_name_remove(domain_name):
    """Test removing a domain name from global list."""
    domain_name.remove()
    assert 'test-domain-name' not in DomainName._all

    domain_name.remove()


def test_domain_name_get(domain_name):
    """Test retrieving a domain name using component ID."""
    assert DomainName.get('test-domain-name') == domain_name

    with pytest.raises(KeyError):
        DomainName.get('unknown-domain-name')


def test_domain_name_list(domain_name):
    """Test that retrieving list of domain name objects."""
    domain_name2 = DomainName('test-domain-name2', 'test.example.com',
                              'test-domain-type', '__all__')
    domains = DomainName.list()
    assert len(domains) == 2
    assert domain_name in domains
    assert domain_name2 in domains

    domains = DomainName.list('http')
    assert len(domains) == 2
    assert domain_name in domains
    assert domain_name2 in domains

    domains = DomainName.list('unknown')
    assert len(domains) == 1
    assert domain_name not in domains
    assert domain_name2 in domains


def test_domain_name_list_names(domain_name):
    """Test that retrieving list of unique domain names works."""
    DomainName('test-domain-name2', 'test.example.com', 'test-domain-type',
               ['http'])
    DomainName('test-domain-name3', 'test3.example.com', 'test-domain-type',
               '__all__')
    domains = DomainName.list_names()
    assert domains == {'test.example.com', 'test3.example.com'}

    domains = DomainName.list_names('http')
    assert domains == {'test.example.com', 'test3.example.com'}

    domains = DomainName.list_names('unknown')
    assert domains == {'test3.example.com'}
