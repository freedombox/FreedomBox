# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the coquelicot module.
"""

from django.conf.urls import url

from .views import CoquelicotAppView

urlpatterns = [
    url(r'^apps/coquelicot/$', CoquelicotAppView.as_view(), name='index'),
]
