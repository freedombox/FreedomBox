# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Privoxy module.
"""

from django.conf.urls import url

from plinth.modules.privoxy import PrivoxyAppView

urlpatterns = [
    url(r'^apps/privoxy/$', PrivoxyAppView.as_view(), name='index'),
]
