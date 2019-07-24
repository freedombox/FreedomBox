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
URLs for the Network module
"""

from django.conf.urls import url

from . import networks as views


urlpatterns = [
    url(r'^sys/networks/$', views.index, name='index'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/show/$', views.show, name='show'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/edit/$', views.edit, name='edit'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/activate/$', views.activate,
        name='activate'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/deactivate/$', views.deactivate,
        name='deactivate'),
    url(r'^sys/networks/scan/$', views.scan, name='scan'),
    url(r'^sys/networks/add/$', views.add, name='add'),
    url(r'^sys/networks/add/generic/$', views.add_generic, name='add_generic'),
    url(r'^sys/networks/add/ethernet/$', views.add_ethernet,
        name='add_ethernet'),
    url(r'^sys/networks/add/pppoe/$', views.add_pppoe, name='add_pppoe'),
    url(r'^sys/networks/add/wifi/(?:(?P<ssid>[^/]+)/'
        r'(?P<interface_name>[^/]+)/)?$',
        views.add_wifi, name='add_wifi'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/delete/$', views.delete,
        name='delete'),
]
