# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Searx module.
"""

from django.conf.urls import url

from .views import SearxAppView

urlpatterns = [
    url(r'^apps/searx/$', SearxAppView.as_view(), name='index'),
]
