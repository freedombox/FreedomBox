# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for Cockpit module.
"""

from django.urls import re_path

from plinth.modules.cockpit.views import CockpitAppView

urlpatterns = [
    re_path(r'^sys/cockpit/$', CockpitAppView.as_view(), name='index'),
]
