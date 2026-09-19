# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the SOGo module."""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^apps/sogo/$', views.SOGoAppView.as_view(), name='index')
]
