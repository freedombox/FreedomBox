# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for Cockpit module.
"""

from django.conf.urls import url

from plinth.modules.cockpit.views import CockpitAppView

urlpatterns = [
    url(r'^sys/cockpit/$', CockpitAppView.as_view(), name='index'),
]
