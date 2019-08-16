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

from .. import on_domain_added, on_domain_removed
from ..components import DomainName, DomainType


@pytest.fixture(name='clean_domains')
def fixture_clean_domains():
    """Test fixture to start a test with clean domains list."""
    DomainName._all = {}  # pylint: disable=protected-access


@pytest.mark.usefixtures('clean_domains')
def test_on_domain_added():
    """Test adding a domain to the global list."""
    on_domain_added('', '')
    assert not DomainName.list()

    DomainType('domain-type-tor', 'Tor Domain', 'torurl')
    on_domain_added('tor', 'domain-type-tor', 'ddddd.onion')
    on_domain_added('tor', 'domain-type-tor', 'eeeee.onion')
    DomainName.get('domain-tor-ddddd.onion')
    DomainName.get('domain-tor-eeeee.onion')


@pytest.mark.usefixtures('clean_domains')
def test_on_domain_removed():
    """Test removing a domain from the global list."""
    DomainType('domain-type-tor', 'Tor Domain', 'torurl')
    on_domain_added('tor', 'domain-type-tor', 'ddddd.onion')
    on_domain_removed('tor', 'domain-type-tor', 'ddddd.onion')
    with pytest.raises(KeyError):
        DomainName.get('domain-tor-ddddd.onion')

    # try to remove things that don't exist
    on_domain_removed('', '')
    with pytest.raises(KeyError):
        on_domain_removed('', 'domainname', 'iiiii')
