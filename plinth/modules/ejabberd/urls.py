# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URL for the Ejabberd module
"""

from django.conf.urls import url

from .views import EjabberdAppView

urlpatterns = [
    url(r'^apps/ejabberd/$', EjabberdAppView.as_view(), name='index')
]
