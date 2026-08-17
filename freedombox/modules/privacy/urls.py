# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the Privacy module."""

from django.urls import re_path

from .views import PrivacyAppView

urlpatterns = [
    re_path(r'^sys/privacy/$', PrivacyAppView.as_view(), name='index'),
]
