# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the OpenVPN module."""

from django.urls import re_path

from plinth.utils import user_group_view

from . import views

urlpatterns = [
    re_path(r'^apps/openvpn/$', views.OpenVPNAppView.as_view(), name='index'),
    re_path(r'^apps/openvpn/profile/$', user_group_view(views.profile, 'vpn'),
            name='profile'),
]
