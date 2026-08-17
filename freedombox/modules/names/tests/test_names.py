# SPDX-License-Identifier: AGPL-3.0-or-later
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
        on_domain_removed('', 'some-domain-type', 'x-unknown-name')
