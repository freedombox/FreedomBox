# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the radicale module.
"""

from django.urls import re_path

from .views import RadicaleAppView

urlpatterns = [
    re_path(r'^apps/radicale/$', RadicaleAppView.as_view(), name='index'),
]
