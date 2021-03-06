# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the OpenVPN module.
"""

from django.conf.urls import url

from plinth.utils import user_group_view

from . import views

urlpatterns = [
    url(r'^apps/openvpn/$', views.OpenVPNAppView.as_view(), name='index'),
    url(r'^apps/openvpn/setup/$', views.setup, name='setup'),
    url(r'^apps/openvpn/ecc/$', views.ecc, name='ecc'),
    url(r'^apps/openvpn/profile/$', user_group_view(views.profile, 'vpn'),
        name='profile'),
]
