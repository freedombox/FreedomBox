# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Network module
"""

from django.conf.urls import url
from stronghold.decorators import public

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
    url(
        r'^sys/networks/add/wifi/(?:(?P<ssid>[^/]+)/'
        r'(?P<interface_name>[^/]+)/)?$', views.add_wifi, name='add_wifi'),
    url(r'^sys/networks/(?P<uuid>[\w.@+-]+)/delete/$', views.delete,
        name='delete'),
    url(r'^sys/networks/router-setup-guide/$',
        views.router_configuration_help_page,
        name='router_setup'),
    url(r'^sys/networks/firstboot/router_setup/$',
        public(views.router_configuration_help_page),
        name='firstboot_router_setup'),
    url(r'^sys/networks/internet-connection-type/$',
        views.internet_connection_type_help_page,
        name='internet_connection_type_setup'),
    url(r'^sys/networks/firstboot/internet_connection_type/$',
        public(views.internet_connection_type_help_page),
        name='firstboot_internet_connection_type'),
]
