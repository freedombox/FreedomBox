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
URLs for the Gitweb module.
"""

from django.conf.urls import url

from .views import CreateRepoView, EditRepoView, GitwebAppView, delete

urlpatterns = [
    url(r'^apps/gitweb/$', GitwebAppView.as_view(), name='index'),
    url(r'^apps/gitweb/create/$', CreateRepoView.as_view(), name='create'),
    url(
        r'^apps/gitweb/(?P<name>[a-zA-Z0-9-._]+)/edit/$',
        EditRepoView.as_view(),
        name='edit',
    ),
    url(
        r'^apps/gitweb/(?P<name>[a-zA-Z0-9-._]+)/delete/$',
        delete,
        name='delete',
    ),
]
