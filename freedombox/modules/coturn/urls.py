# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Coturn module.
"""

from django.urls import re_path

from .views import CoturnAppView

urlpatterns = [
    re_path(r'^apps/coturn/$', CoturnAppView.as_view(), name='index'),
]
