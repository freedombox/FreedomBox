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
URLs for the Network module
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'plinth.modules.network.network',
    url(r'^sys/network/$', 'index', name='index'),
    url(r'^sys/network/(?P<conn_id>[\w.@+-]+)/edit/$',
        'edit', name='edit'),
    url(r'^sys/network/(?P<conn_id>[\w.@+-]+)/activate/$',
        'activate', name='activate'),
    url(r'^sys/network/(?P<conn_id>[\w.@+-]+)/deactivate/$',
        'deactivate', name='deactivate'),
    url(r'^sys/network/add/$', 'add', name='add'),
    url(r'^sys/network/add/ethernet/$', 'add_ethernet', name='add_ethernet'),
    url(r'^sys/network/add/wifi/$', 'add_wifi', name='add_wifi'),
    url(r'^sys/network/(?P<conn_id>[\w.@+-]+)/delete/$',
        'delete', name='delete'),
)
