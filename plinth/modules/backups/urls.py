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
URLs for the backups module.
"""

from django.conf.urls import url

from .views import IndexView, CreateArchiveView, DeleteArchiveView, \
    ExtractArchiveView, ExportArchiveView

urlpatterns = [
    url(r'^sys/backups/$', IndexView.as_view(), name='index'),
    url(r'^sys/backups/create/$', CreateArchiveView.as_view(), name='create'),
    url(r'^sys/backups/(?P<name>[a-z0-9]+)/delete/$',
        DeleteArchiveView.as_view(), name='delete'),
    url(r'^sys/backups/(?P<name>[a-z0-9]+)/extract/$',
        ExtractArchiveView.as_view(), name='extract'),
    url(r'^sys/backups/(?P<name>[a-z0-9]+)/export/$',
        ExportArchiveView.as_view(), name='export'),
]
