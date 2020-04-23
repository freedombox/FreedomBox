# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Coturn module.
"""

from django.conf.urls import url

from .views import CoturnAppView

urlpatterns = [
    url(r'^apps/coturn/$', CoturnAppView.as_view(), name='index'),
]
