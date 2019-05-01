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
Test Apache configuration generation for diaspora*
"""

import os
import tempfile

from plinth.modules import diaspora


def test_generate_apache_configuration():
    """Test that Apache configuration is created properly."""
    with tempfile.NamedTemporaryFile() as conf_file:
        diaspora.generate_apache_configuration(conf_file.name,
                                               'freedombox.rocks')

        assert os.stat(conf_file.name).st_size != 0

        with open(conf_file.name) as file_handle:
            contents = file_handle.read()

        assert all(
            word in contents
            for word in ['VirtualHost', 'Location', 'Directory', 'assets'])
