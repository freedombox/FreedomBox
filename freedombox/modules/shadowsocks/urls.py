# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Shadowsocks Clients.
"""

from django.urls import re_path

from .views import ShadowsocksAppView

urlpatterns = [
    re_path(r'^apps/shadowsocks/$', ShadowsocksAppView.as_view(),
            name='index'),
]
