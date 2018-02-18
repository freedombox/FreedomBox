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
URLs for the sharing app.
"""

from django.conf.urls import url

from .views import AddShareView, EditShareView, IndexView, remove

urlpatterns = [
    url(r'^apps/sharing/$', IndexView.as_view(), name='index'),
    url(r'^apps/sharing/add/$', AddShareView.as_view(), name='add'),
    url(r'^apps/sharing/(?P<name>[a-z0-9]+)/edit/$', EditShareView.as_view(),
        name='edit'),
    url(r'^apps/sharing/(?P<name>[a-z0-9]+)/remove/$', remove, name='remove'),
]
