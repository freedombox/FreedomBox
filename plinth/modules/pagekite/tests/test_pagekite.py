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
Test modules for Pagekite functions.
"""

from plinth.modules.pagekite import utils


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


def test_convert_service_to_string():
    """ Test deconstructing parameter dictionaries into strings """
    for test in _tests:
        service_string = utils.convert_service_to_string(test['params'])
        assert test['line'] == service_string
