# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Transmission module.
"""

from django.conf.urls import url

from .views import TransmissionAppView

urlpatterns = [
    url(r'^apps/transmission/$', TransmissionAppView.as_view(), name='index'),
]
