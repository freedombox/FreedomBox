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

from .views import IndexView, CreateArchiveView, DownloadArchiveView, \
    ExportArchiveView, DeleteArchiveView, RestoreView

urlpatterns = [
    url(r'^sys/backups/$', IndexView.as_view(), name='index'),
    url(r'^sys/backups/create/$', CreateArchiveView.as_view(), name='create'),
    url(r'^sys/backups/export/(?P<name>[^/]+)/$',
        ExportArchiveView.as_view(), name='export'),
    url(r'^sys/backups/download/(?P<label>[^/]+)/(?P<name>[^/]+)/$',
        DownloadArchiveView.as_view(), name='download'),
    url(r'^sys/backups/delete/(?P<name>[^/]+)/$',
        DeleteArchiveView.as_view(), name='delete'),
    url(r'^sys/backups/restore/(?P<label>[^/]+)/(?P<name>[^/]+)/$',
        RestoreView.as_view(), name='restore'),
]
