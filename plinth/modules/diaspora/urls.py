# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the diaspora module
"""

from django.urls import re_path

from .views import DiasporaAppView, DiasporaSetupView

urlpatterns = [
    re_path(r'^apps/diaspora/setup$', DiasporaSetupView.as_view(),
            name='setup'),
    re_path(r'^apps/diaspora/$', DiasporaAppView.as_view(), name='index')
]
