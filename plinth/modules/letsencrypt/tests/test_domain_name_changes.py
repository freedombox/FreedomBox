#
# This file is part of Plinth.
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

import unittest

from .. import on_domain_added, on_domain_removed


class TestDomainNameChanges(unittest.TestCase):
    """Test for automatically obtaining and revoking Let's Encrypt certs"""

    def test_add_onion_domain(self):
        self.assertFalse(
            on_domain_added('test', 'hiddenservice', 'ddddd.onion'))

    def test_add_valid_domain(self):
        self.assertTrue(
            on_domain_added('test', 'domainname', 'subdomain.domain.tld'))

    def test_remove_domain(self):
        self.assertTrue(on_domain_removed('test', '', 'somedomain.tld'))
