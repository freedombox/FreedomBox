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
Django models for the main application
"""

from collections import namedtuple

web_client = namedtuple('Web_Client', ['name', 'url'])

desktop_client = namedtuple('Desktop_clients', ['name', 'url'])

mobile_client = namedtuple('Mobile_clients', ['name',
                                              'fully_qualified_name',
                                              'fdroid_url', 'play_store_url'])
