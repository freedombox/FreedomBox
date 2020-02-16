# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the radicale module.
"""

from django.conf.urls import url

from .views import RadicaleAppView

urlpatterns = [
    url(r'^apps/radicale/$', RadicaleAppView.as_view(), name='index'),
]
