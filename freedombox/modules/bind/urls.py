# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the BIND module.
"""

from django.urls import re_path

from plinth.modules.bind.views import BindAppView

urlpatterns = [
    re_path(r'^sys/bind/$', BindAppView.as_view(), name='index'),
]
