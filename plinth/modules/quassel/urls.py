# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the quassel module.
"""

from django.conf.urls import url

from .views import QuasselAppView

urlpatterns = [
    url(r'^apps/quassel/$', QuasselAppView.as_view(), name='index'),
]
