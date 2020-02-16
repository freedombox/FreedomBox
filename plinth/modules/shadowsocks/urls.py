# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Shadowsocks module.
"""

from django.conf.urls import url

from .views import ShadowsocksAppView

urlpatterns = [
    url(r'^apps/shadowsocks/$', ShadowsocksAppView.as_view(), name='index'),
]
