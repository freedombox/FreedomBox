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

import pytest

from .. import on_domain_added, on_domain_removed

pytestmark = pytest.mark.usefixtures('needs_root', 'needs_sudo')


def test_add_onion_domain():
    assert not on_domain_added('test', 'hiddenservice', 'ddddd.onion')


@pytest.mark.usefixtures('load_cfg')
def test_add_valid_domain():
    assert on_domain_added('test', 'domainname', 'subdomain.domain.tld')


def test_remove_domain():
    assert on_domain_removed('test', '', 'somedomain.tld')
