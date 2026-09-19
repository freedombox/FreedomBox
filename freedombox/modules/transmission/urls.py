# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Transmission module.
"""

from django.urls import re_path

from .views import TransmissionAppView

urlpatterns = [
    re_path(r'^apps/transmission/$', TransmissionAppView.as_view(),
            name='index'),
]
