# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Searx module.
"""

from django.urls import re_path

from .views import SearxAppView

urlpatterns = [
    re_path(r'^apps/searx/$', SearxAppView.as_view(), name='index'),
]
