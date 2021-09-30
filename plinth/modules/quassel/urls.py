# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the quassel module.
"""

from django.urls import re_path

from .views import QuasselAppView

urlpatterns = [
    re_path(r'^apps/quassel/$', QuasselAppView.as_view(), name='index'),
]
