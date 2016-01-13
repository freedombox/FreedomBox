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
Tests for names module.
"""

import unittest

from .. import domain_types, domains
from .. import on_domain_added, on_domain_removed
from .. import get_domain_types, get_description
from .. import get_domain, get_enabled_services, get_services_status


class TestNames(unittest.TestCase):
    """Test cases for testing the names module."""
    def test_on_domain_added(self):
        """Test adding a domain to the global list."""
        on_domain_added('', '')
        self.assertNotIn('', domain_types)
        self.assertNotIn('', domains)

        on_domain_added('', 'hiddenservice', 'ddddd.onion')
        on_domain_added('', 'hiddenservice', 'eeeee.onion')
        self.assertIn('ddddd.onion', domains['hiddenservice'])
        self.assertIn('eeeee.onion', domains['hiddenservice'])

    def test_on_domain_removed(self):
        """Test removing a domain from the global list."""
        on_domain_added('', 'domainname', 'fffff')
        on_domain_removed('', 'domainname', 'fffff')
        self.assertNotIn('fffff', domains['domainname'])

        on_domain_added('', 'pagekite', 'ggggg.pagekite.me')
        on_domain_added('', 'pagekite', 'hhhhh.pagekite.me')
        on_domain_removed('', 'pagekite')
        self.assertNotIn('ggggg.pagekite.me', domains['pagekite'])
        self.assertNotIn('hhhhh.pagekite.me', domains['pagekite'])

        # try to remove things that don't exist
        on_domain_removed('', '')
        on_domain_removed('', 'domainname', 'iiiii')

    def test_get_domain_types(self):
        """Test getting domain types."""
        on_domain_added('', 'domainname')
        self.assertIn('domainname', get_domain_types())

    def test_get_description(self):
        """Test getting domain type description."""
        on_domain_added('', 'pagekite', '', 'Pagekite')
        self.assertEqual(get_description('pagekite'), 'Pagekite')

        self.assertEqual('asdfasdf', get_description('asdfasdf'))

    def test_get_domain(self):
        """Test getting a domain of domain_type."""
        on_domain_added('', 'hiddenservice', 'aaaaa.onion')
        self.assertEqual(get_domain('hiddenservice'), 'aaaaa.onion')

        self.assertEqual(None, get_domain('abcdef'))

        on_domain_removed('', 'hiddenservice')
        self.assertEqual(None, get_domain('hiddenservice'))

    def test_get_enabled_services(self):
        """Test getting enabled services for a domain."""
        on_domain_added('', 'domainname', 'bbbbb', '',
                        ['http', 'https', 'ssh'])
        self.assertEqual(get_enabled_services('domainname', 'bbbbb'),
                         ['http', 'https', 'ssh'])

        self.assertEqual(get_enabled_services('xxxxx', 'yyyyy'), [])
        self.assertEqual(get_enabled_services('domainname', 'zzzzz'), [])

    def test_get_services_status(self):
        """Test getting whether each service is enabled for a domain."""
        on_domain_added('', 'pagekite', 'ccccc.pagekite.me', '',
                        ['http', 'https'])
        self.assertEqual(get_services_status('pagekite', 'ccccc.pagekite.me'),
                         [True, True, False])
