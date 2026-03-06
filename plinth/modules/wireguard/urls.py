# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the wireguard module.
"""

from django.urls import re_path

from plinth.modules.wireguard import views

urlpatterns = [
    re_path(r'^apps/wireguard/$', views.WireguardView.as_view(), name='index'),
    re_path(r'^apps/wireguard/enable-server/$',
            views.EnableServerView.as_view(), name='enable-server'),
    re_path(r'^apps/wireguard/client/add/$', views.AddClientView.as_view(),
            name='add-client'),
    re_path(r'^apps/wireguard/client/(?P<public_key>[^/]+)/show/$',
            views.ShowClientView.as_view(), name='show-client'),
    re_path(r'^apps/wireguard/client/(?P<public_key>[^/]+)/edit/$',
            views.EditClientView.as_view(), name='edit-client'),
    re_path(r'^apps/wireguard/client/(?P<public_key>[^/]+)/delete/$',
            views.DeleteClientView.as_view(), name='delete-client'),
    re_path(r'^apps/wireguard/server/add/$', views.AddServerView.as_view(),
            name='add-server'),
    re_path(r'^apps/wireguard/server/(?P<interface>wg[0-9]+)/show/$',
            views.ShowServerView.as_view(), name='show-server'),
    re_path(r'^apps/wireguard/server/(?P<interface>wg[0-9]+)/edit/$',
            views.EditServerView.as_view(), name='edit-server'),
    re_path(r'^apps/wireguard/server/(?P<interface>wg[0-9]+)/delete/$',
            views.DeleteServerView.as_view(), name='delete-server'),
]
