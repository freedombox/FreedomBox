# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for Cockpit module.
"""

from django.urls import re_path

from plinth.views import AppView

urlpatterns = [
    re_path(r'^sys/cockpit/$', AppView.as_view(app_id='cockpit'),
            name='index'),
]
