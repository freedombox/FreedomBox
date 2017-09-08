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
URLs for the plinth api for android app.
"""

from django.conf.urls import url
from stronghold.decorators import public

from plinth.modules.api.views import get_apps, get_access_info

urlpatterns = [
    url(r'^api/(?P<version>[0-9]+)/services/?$', public(get_apps)),
    url(r'^api/(?P<version>[0-9]+)/access-info/?$', public(get_access_info))
]