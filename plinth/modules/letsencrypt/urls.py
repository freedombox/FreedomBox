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
URLs for the Let's Encrypt module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/letsencrypt/$', views.index, name='index'),
    url(r'^sys/letsencrypt/revoke/(?P<domain>[^/]+)/$', views.revoke,
        name='revoke'),
    url(r'^sys/letsencrypt/obtain/(?P<domain>[^/]+)/$', views.obtain,
        name='obtain'),
    url(r'^sys/letsencrypt/delete/(?P<domain>[^/]+)/$', views.delete,
        name='delete'),
]
