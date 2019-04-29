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

import unittest

from plinth.modules.i2p.helpers import RouterEditor
from plinth.modules.i2p.tests import DATA_DIR

ROUTER_CONF_PATH = str(DATA_DIR / 'router.config')


class RouterEditingTests(unittest.TestCase):

    def setUp(self):
        self.editor = RouterEditor(ROUTER_CONF_PATH)

    def test_count_favs(self):
        self.editor.read_conf()
        favs = self.editor.get_favorites()
        self.assertEqual(len(favs.keys()), 17)

    def test_add_normal_favorite(self):
        self.editor.read_conf()
        name = 'Somewhere'
        url = 'http://somewhere-again.i2p'
        description = "Just somewhere else"
        self.editor.add_favorite(
            name, url, description
        )

        favs = self.editor.get_favorites()
        self.assertIn(url, favs)
        favorite = favs[url]
        self.assertEqual(favorite['name'], name)
        self.assertEqual(favorite['description'], description)

        self.assertEqual(len(favs), 18)

    def test_add_favorite_with_comma(self):
        self.editor.read_conf()
        name = 'Name,with,comma'
        expected_name = name.replace(',', '.')
        url = 'http://url-without-comma.i2p'
        description = "Another,comma,to,play,with"
        expected_description = description.replace(',', '.')

        self.editor.add_favorite(
            name, url, description
        )

        favs = self.editor.get_favorites()
        self.assertIn(url, favs)
        favorite = favs[url]
        self.assertEqual(favorite['name'], expected_name)
        self.assertEqual(favorite['description'], expected_description)

        self.assertEqual(len(favs), 18)

    def test_add_fav_to_empty_config(self):
        self.editor.conf_filename = '/tmp/inexistent.conf'
        self.editor.read_conf()
        self.assertEqual(len(self.editor.get_favorites()), 0)

        name = 'Test Favorite'
        url = 'http://test-fav.i2p'
        self.editor.add_favorite(
            name, url
        )
        self.assertEqual(len(self.editor.get_favorites()), 1)


if __name__ == '__main__':
    unittest.main()
