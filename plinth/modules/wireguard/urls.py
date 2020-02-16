# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the wireguard module.
"""

from django.conf.urls import url

from plinth.modules.wireguard import views

urlpatterns = [
    url(r'^apps/wireguard/$', views.WireguardView.as_view(), name='index'),
    url(r'^apps/wireguard/client/add/$', views.AddClientView.as_view(),
        name='add-client'),
    url(r'^apps/wireguard/client/(?P<public_key>[^/]+)/show/$',
        views.ShowClientView.as_view(), name='show-client'),
    url(r'^apps/wireguard/client/(?P<public_key>[^/]+)/edit/$',
        views.EditClientView.as_view(), name='edit-client'),
    url(r'^apps/wireguard/client/(?P<public_key>[^/]+)/delete/$',
        views.DeleteClientView.as_view(), name='delete-client'),
    url(r'^apps/wireguard/server/add/$', views.AddServerView.as_view(),
        name='add-server'),
    url(r'^apps/wireguard/server/(?P<interface>wg[0-9]+)/show/$',
        views.ShowServerView.as_view(), name='show-server'),
    url(r'^apps/wireguard/server/(?P<interface>wg[0-9]+)/edit/$',
        views.EditServerView.as_view(), name='edit-server'),
    url(r'^apps/wireguard/server/(?P<interface>wg[0-9]+)/delete/$',
        views.DeleteServerView.as_view(), name='delete-server'),
]
