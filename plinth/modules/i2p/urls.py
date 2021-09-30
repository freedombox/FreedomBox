# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the I2P module.
"""

from django.urls import re_path

from plinth.modules.i2p import views

urlpatterns = [
    re_path(r'^apps/i2p/$', views.I2PAppView.as_view(), name='index')
]
