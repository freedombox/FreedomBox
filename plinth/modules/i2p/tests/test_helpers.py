#  This file is part of FreedomBox.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import unittest

from pathlib import Path

from plinth.modules.i2p.helpers import TunnelEditor

DATA_DIR = Path(__file__).parent / 'data'
TUNNEL_CONF_PATH = DATA_DIR / 'i2ptunnel.config'
TUNNEL_HTTP_NAME = 'I2P HTTP Proxy'


class TunnelEditorTests(unittest.TestCase):

    def setUp(self):
        self.editor = TunnelEditor(str(TUNNEL_CONF_PATH))

    def test_reading_conf(self):
        self.editor.read_conf()
        self.assertGreater(len(self.editor.lines), 1)

    def test_setting_idx(self):
        self.editor.read_conf()
        self.assertIsNone(self.editor.idx)
        self.editor.set_tunnel_idx(TUNNEL_HTTP_NAME)
        self.assertEqual(self.editor.idx, 0)

    def test_setting_tunnel_props(self):
        self.editor.read_conf()
        self.editor.set_tunnel_idx('I2P HTTP Proxy')
        interface = '0.0.0.0'
        self.editor.set_tunnel_prop('interface', interface)
        self.assertEqual(self.editor['interface'], interface)

    def test_getting_inexistent_props(self):
        self.editor.read_conf()
        self.editor.idx = 0
        self.assertRaises(KeyError, self.editor.__getitem__, 'blabla')

    def test_setting_new_props(self):
        self.editor.read_conf()
        self.editor.idx = 0
        value = 'lol'
        prop = 'blablabla'
        self.editor[prop] = value
        self.assertEqual(self.editor[prop], value)


if __name__ == '__main__':
    unittest.main()
