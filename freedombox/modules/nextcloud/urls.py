# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the Nextcloud module."""

from django.urls import re_path

from .views import NextcloudAppView

urlpatterns = [
    re_path(r'^apps/nextcloud/$', NextcloudAppView.as_view(), name='index')
]
