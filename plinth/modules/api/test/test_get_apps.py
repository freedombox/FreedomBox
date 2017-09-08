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
Test get apps for api module.
"""

import unittest

from plinth.modules.api.views import get_app_payload


class TestApi(unittest.TestCase):
    apps = [{
        'name': 'someName',
        'short_description': 'someDescription',
        'icon': 'someIconURl',
        'label': 'someLabel'
    }]

    expected = [{
        'name': 'someName',
        'short_description': 'someDescription',
        'icon': 'static/theme/icons/someIconURl.svg'
    }]

    def test_get_app_payload(self):
        apps = get_app_payload(self.apps)
        self.assertEquals(apps, self.expected)