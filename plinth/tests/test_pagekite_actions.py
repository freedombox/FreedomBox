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

import os
import unittest

from actions.pagekite_util import get_augeas_servicefile_path, CONF_PATH, \
    construct_params, deconstruct_params


class TestPagekiteActions(unittest.TestCase):
    # test-cases to convert parameter-strings into param dicts and back
    _tests = [
        {
            'line': 'https/8080:*.@kitename:localhost:8080:@kitesecret',
            'params': {'kitename': '*.@kitename', 'backend_host': 'localhost',
                       'secret': '@kitesecret', 'protocol': 'https/8080',
                       'backend_port': '8080'}
        },
        {
            'line': 'https:*.@kitename:localhost:80:@kitesecret',
            'params': {'protocol': 'https',
                       'kitename': '*.@kitename',
                       'backend_port': '80',
                       'backend_host': 'localhost',
                       'secret': '@kitesecret'}
        },
        {
            'line': 'raw/22:@kitename:localhost:22:@kitesecret',
            'params': {'protocol': 'raw/22',
                       'kitename': '@kitename',
                       'backend_port': '22',
                       'backend_host': 'localhost',
                       'secret': '@kitesecret'}
        },
    ]

    def test_get_augeas_servicefile_path(self):
        """ Test the generation of augeas-paths for pagekite services """
        tests = (('http', '80_http.rc'),
                 ('https', '443_https.rc'),
                 ('http/80', '80_http.rc'),
                 ('http/8080', '8080_http.rc'),
                 ('raw/22', '22_raw.rc'))
        for protocol, filename in tests:
            expected_path = os.path.join(CONF_PATH, filename, 'service_on')
            returned_path = get_augeas_servicefile_path(protocol)
            self.assertEqual(expected_path, returned_path)

        with self.assertRaises(ValueError):
            get_augeas_servicefile_path('xmpp')

    def test_deconstruct_params(self):
        """ Test deconstructing parameter dictionaries into strings """
        for test in self._tests:
            self.assertEqual(test['line'], deconstruct_params(test['params']))

    def test_construct_params(self):
        """ Test constructing parameter dictionaries out of string """
        for test in self._tests:
            self.assertEqual(test['params'], construct_params(test['line']))

        line = "'https/80'; touch /etc/fstab':*.@kitename:localhost:80:foo'"
        with self.assertRaises(RuntimeError):
            construct_params(line)
