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
Test actions for configuring bind
"""

import tempfile
import unittest

from plinth.modules import bind


class TestBind(unittest.TestCase):
    """Test actions for configuring bind."""

    def setUp(self):
        self.conf_file = tempfile.NamedTemporaryFile()
        with open(self.conf_file.name, 'w') as conf:
            conf.write(bind.DEFAULT_CONFIG)

        bind.CONFIG_FILE = self.conf_file.name

    def test_set_forwarders(self):
        bind.set_forwarders('8.8.8.8 8.8.4.4')
        conf = bind.get_config()
        self.assertEqual(conf['forwarders'], '8.8.8.8 8.8.4.4')

        bind.set_forwarders('')
        conf = bind.get_config()
        self.assertEqual(conf['forwarders'], '')

    def test_enable_dnssec(self):
        bind.set_dnssec('enable')
        conf = bind.get_config()
        self.assertEqual(conf['enable_dnssec'], True)

        bind.set_dnssec('disable')
        conf = bind.get_config()
        self.assertEqual(conf['enable_dnssec'], False)
