# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URL for the Ejabberd module
"""

from django.urls import re_path

from .views import EjabberdAppView

urlpatterns = [
    re_path(r'^apps/ejabberd/$', EjabberdAppView.as_view(), name='index')
]
