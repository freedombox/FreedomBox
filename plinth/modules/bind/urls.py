# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the BIND module.
"""

from django.conf.urls import url

from plinth.modules.bind.views import BindAppView

urlpatterns = [
    url(r'^sys/bind/$', BindAppView.as_view(), name='index'),
]
