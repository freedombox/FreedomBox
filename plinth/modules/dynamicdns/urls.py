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
URLs for the dynamicdns module
"""

from django.conf.urls import url

from . import dynamicdns as views


urlpatterns = [
    url(r'^apps/dynamicdns/$', views.index, name='index'),
    url(r'^apps/dynamicdns/configure/$', views.configure, name='configure'),
    url(r'^apps/dynamicdns/statuspage/$', views.statuspage, name='statuspage'),
]
