# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Roundcube module.
"""

from django.urls import re_path

from .views import RoundcubeAppView

urlpatterns = [
    re_path(r'^apps/roundcube/$', RoundcubeAppView.as_view(), name='index')
]
