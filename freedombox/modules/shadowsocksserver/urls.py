# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Shadowsocks Server module.
"""

from django.urls import re_path

from .views import ShadowsocksServerAppView

urlpatterns = [
    re_path(r'^apps/shadowsocksserver/$', ShadowsocksServerAppView.as_view(),
            name='index'),
]
