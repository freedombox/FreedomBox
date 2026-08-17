# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Network module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/networks/$', views.NetworksAppView.as_view(), name='index'),
    re_path(r'^sys/networks/(?P<uuid>[\w.@+-]+)/show/$', views.show,
            name='show'),
    re_path(r'^sys/networks/(?P<uuid>[\w.@+-]+)/edit/$', views.edit,
            name='edit'),
    re_path(r'^sys/networks/(?P<uuid>[\w.@+-]+)/activate/$', views.activate,
            name='activate'),
    re_path(r'^sys/networks/(?P<uuid>[\w.@+-]+)/deactivate/$',
            views.deactivate, name='deactivate'),
    re_path(r'^sys/networks/scan/$', views.scan, name='scan'),
    re_path(r'^sys/networks/add/$', views.add, name='add'),
    re_path(r'^sys/networks/add/generic/$', views.add_generic,
            name='add_generic'),
    re_path(r'^sys/networks/add/ethernet/$', views.add_ethernet,
            name='add_ethernet'),
    re_path(r'^sys/networks/add/pppoe/$', views.add_pppoe, name='add_pppoe'),
    re_path(
        r'^sys/networks/add/wifi/(?:(?P<ssid>[^/]+)/'
        r'(?P<interface_name>[^/]+)/)?$', views.add_wifi, name='add_wifi'),
    re_path(r'^sys/networks/(?P<uuid>[\w.@+-]+)/delete/$', views.delete,
            name='delete'),
    re_path(r'^sys/networks/router-configuration/$',
            views.RouterConfigurationView.as_view(),
            name='router-configuration'),
    re_path(r'^sys/networks/internet-connection-type/$',
            views.InternetConnectionTypeView.as_view(),
            name='internet-connection-type'),
    re_path(r'^sys/networks/network-topology/$',
            views.NetworkTopologyView.as_view(), name='network-topology'),
]
