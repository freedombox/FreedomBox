# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Deluge module.
"""

from django.conf.urls import url

from .views import DelugeAppView

urlpatterns = [
    url(r'^apps/deluge/$', DelugeAppView.as_view(), name='index')
]
