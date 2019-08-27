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
URLs for the Help module
"""

from django.conf.urls import url

from plinth.utils import non_admin_view

from . import help as views

urlpatterns = [
    url(r'^help/$', non_admin_view(views.index), name='index'),
    url(r'^help/about/$', non_admin_view(views.about), name='about'),
    url(r'^help/feedback/$', non_admin_view(views.feedback), name='feedback'),
    url(r'^help/manual/$', non_admin_view(views.manual), name='manual'),
    url(r'^help/manual/download/$', non_admin_view(views.download_manual),
        name='download-manual'),
    url(r'^help/manual/(?P<page>[\w-]+)?/?$', non_admin_view(views.manual),
        name='manual-page'),
    url(r'^help/status-log/$', non_admin_view(views.status_log),
        name='status-log'),
]
