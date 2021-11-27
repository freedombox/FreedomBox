# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Tiny Tiny RSS module.
"""

from django.urls import re_path

from .views import TTRSSAppView

urlpatterns = [re_path(r'^apps/ttrss/$', TTRSSAppView.as_view(), name='index')]
