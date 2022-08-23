# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Tor module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^apps/tor/$', views.TorAppView.as_view(), name='index'),
]
