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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from plinth.modules.sso import auth_pubtkt_util
from plinth.modules.sso.constants import private_key_file_name, \
    public_key_file_name
from OpenSSL import crypto

import os
import unittest
import tempfile


class TestAuthPubTKTUtil(unittest.TestCase):
    def test_create_key_pair(self):
        with tempfile.TemporaryDirectory() as tdir:
            auth_pubtkt_util.create_key_pair(tdir)

            private_key_file = os.path.join(tdir, private_key_file_name)
            public_key_file = os.path.join(tdir, public_key_file_name)

            # key files are created
            assert os.path.exists(private_key_file)
            assert os.path.exists(public_key_file)

            # keys can be retrieved from the files
            with open(private_key_file, 'r') as fil:
                assert crypto.load_privatekey(crypto.FILETYPE_PEM,
                                              fil.read().encode())

            with open(public_key_file, 'r') as fil:
                assert crypto.load_publickey(crypto.FILETYPE_PEM,
                                             fil.read().encode())

    def test_generate_ticket(self):
        with tempfile.TemporaryDirectory() as tdir:
            auth_pubtkt_util.create_key_pair(tdir)

            private_key_file = os.path.join(tdir, private_key_file_name)

            ticket = auth_pubtkt_util.generate_ticket(
                "some_user", private_key_file, tokens=["admin", "wiki"])

            assert "uid=some_user" in ticket
            assert "validuntil" in ticket
