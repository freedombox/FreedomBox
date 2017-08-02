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
Test Apache configuration generation for diaspora*
"""

import os
import unittest
from plinth.modules import diaspora


class TestDiaspora(unittest.TestCase):
    def test_generate_apache_configuration(self):
        test_root = "/tmp/apache2/conf-available/"
        conf_file = test_root + "diaspora-plinth.conf"
        os.path.exists(test_root) or os.makedirs(test_root)
        diaspora.generate_apache_configuration(conf_file, "freedombox.rocks")

        assert os.stat(conf_file).st_size != 0

        with open(conf_file) as f:
            contents = f.read()
        assert all(w in contents
                   for w in ['VirtualHost', 'Location', 'Directory', 'assets'])
