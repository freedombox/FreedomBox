# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Deluge module.
"""

from django.urls import re_path

from .views import DelugeAppView

urlpatterns = [
    re_path(r'^apps/deluge/$', DelugeAppView.as_view(), name='index')
]
