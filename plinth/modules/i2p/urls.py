# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the I2P module.
"""

from django.conf.urls import url

from plinth.modules.i2p import views

urlpatterns = [
    url(r'^apps/i2p/$', views.I2PAppView.as_view(), name='index'),
    url(r'^apps/i2p/tunnels/?$', views.TunnelsView.as_view(), name='tunnels'),
    url(r'^apps/i2p/torrents/?$', views.TorrentsView.as_view(),
        name='torrents'),
]
