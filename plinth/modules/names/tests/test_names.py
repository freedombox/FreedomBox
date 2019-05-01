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
Tests for names module.
"""

import pytest

from .. import domain_types, domains
from .. import on_domain_added, on_domain_removed
from .. import get_domain_types, get_description
from .. import get_domain, get_enabled_services, get_services_status


@pytest.fixture(name='clean_domains')
def fixture_clean_domains():
    """Test fixture to start a test with clean domains list."""
    old_domain_types = dict(domain_types)
    old_domains = dict(domains)
    domain_types.clear()
    domains.clear()
    yield
    domain_types.clear()
    domains.clear()
    domain_types.update(old_domain_types)
    domains.update(old_domains)


@pytest.mark.usefixtures('clean_domains')
def test_on_domain_added():
    """Test adding a domain to the global list."""
    on_domain_added('', '')
    assert '' not in domain_types
    assert '' not in domains

    on_domain_added('', 'hiddenservice', 'ddddd.onion')
    on_domain_added('', 'hiddenservice', 'eeeee.onion')
    assert 'ddddd.onion' in domains['hiddenservice']
    assert 'eeeee.onion' in domains['hiddenservice']


@pytest.mark.usefixtures('clean_domains')
def test_on_domain_removed():
    """Test removing a domain from the global list."""
    on_domain_added('', 'domainname', 'fffff')
    on_domain_removed('', 'domainname', 'fffff')
    assert 'fffff' not in domains['domainname']

    on_domain_added('', 'pagekite', 'ggggg.pagekite.me')
    on_domain_added('', 'pagekite', 'hhhhh.pagekite.me')
    on_domain_removed('', 'pagekite')
    assert 'ggggg.pagekite.me' not in domains['pagekite']
    assert 'hhhhh.pagekite.me' not in domains['pagekite']

    # try to remove things that don't exist
    on_domain_removed('', '')
    on_domain_removed('', 'domainname', 'iiiii')


@pytest.mark.usefixtures('clean_domains')
def test_get_domain_types():
    """Test getting domain types."""
    on_domain_added('', 'domainname')
    assert 'domainname' in get_domain_types()


@pytest.mark.usefixtures('clean_domains')
def test_get_description():
    """Test getting domain type description."""
    on_domain_added('', 'pagekite', '', 'Pagekite')
    assert get_description('pagekite') == 'Pagekite'

    assert get_description('asdfasdf') == 'asdfasdf'


@pytest.mark.usefixtures('clean_domains')
def test_get_domain():
    """Test getting a domain of domain_type."""
    on_domain_added('', 'hiddenservice', 'aaaaa.onion')
    assert get_domain('hiddenservice') == 'aaaaa.onion'

    assert get_domain('abcdef') is None

    on_domain_removed('', 'hiddenservice')
    assert get_domain('hiddenservice') is None


@pytest.mark.usefixtures('clean_domains')
def test_get_enabled_services():
    """Test getting enabled services for a domain."""
    on_domain_added('', 'domainname', 'bbbbb', '', ['http', 'https', 'ssh'])
    assert get_enabled_services('domainname',
                                'bbbbb') == ['http', 'https', 'ssh']

    assert get_enabled_services('xxxxx', 'yyyyy') == []
    assert get_enabled_services('domainname', 'zzzzz') == []


@pytest.mark.usefixtures('clean_domains')
def test_get_services_status():
    """Test getting whether each service is enabled for a domain."""
    on_domain_added('', 'pagekite', 'ccccc.pagekite.me', '', ['http', 'https'])
    assert get_services_status('pagekite', 'ccccc.pagekite.me') == \
        [True, True, False]
