# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Network module
"""

from django.conf.urls import url

from . import views

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
    url(r'^sys/networks/router-configuration/$',
        views.RouterConfigurationView.as_view(), name='router-configuration'),
    url(r'^sys/networks/firstboot/router-configuration/$',
        views.RouterConfigurationFirstBootView.as_view(),
        name='router-configuration-first-boot'),
    url(r'^sys/networks/internet-connection-type/$',
        views.InternetConnectionTypeView.as_view(),
        name='internet-connection-type'),
    url(r'^sys/networks/firstboot/internet-connection-type/$',
        views.InternetConnectionTypeFirstBootView.as_view(),
        name='internet-connection-type-first-boot'),
    url(r'^sys/networks/network-topology/$',
        views.NetworkTopologyView.as_view(), name='network-topology'),
    url(r'^sys/networks/firstboot/network-topology-first-boot/$',
        views.NetworkTopologyFirstBootView.as_view(),
        name='network-topology-first-boot'),
]
