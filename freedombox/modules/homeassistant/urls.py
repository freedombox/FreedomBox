# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the Home Assistant module."""

from django.urls import re_path

from .views import HomeAssistantAppView

urlpatterns = [
    re_path(r'^apps/homeassistant/$', HomeAssistantAppView.as_view(),
            name='index')
]
