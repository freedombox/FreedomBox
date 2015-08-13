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
    'plinth.modules.networks.networks',
    url(r'^sys/networks/$', 'index', name='index'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/edit/$',
        'edit', name='edit'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/activate/$',
        'activate', name='activate'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/deactivate/$',
        'deactivate', name='deactivate'),
    url(r'^sys/networks/scan/$', 'scan', name='scan'),
    url(r'^sys/networks/add/$', 'add', name='add'),
    url(r'^sys/networks/add/ethernet/$', 'add_ethernet', name='add_ethernet'),
    url(r'^sys/networks/add/pppoe/$', 'add_pppoe', name='add_pppoe'),
    url(r'^sys/networks/add/wifi/(?:(?P<ssid>[^/]+)/)?$', 'add_wifi',
        name='add_wifi'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/delete/$',
        'delete', name='delete'),
)
