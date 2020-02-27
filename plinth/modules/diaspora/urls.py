# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the diaspora module
"""

from django.conf.urls import url

from .views import DiasporaAppView, DiasporaSetupView

urlpatterns = [
    url(r'^apps/diaspora/setup$', DiasporaSetupView.as_view(), name='setup'),
    url(r'^apps/diaspora/$', DiasporaAppView.as_view(), name='index')
]
