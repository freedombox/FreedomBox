# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the service discovery module.
"""

from django.urls import re_path

from plinth.views import AppView

urlpatterns = [
    re_path(r'^sys/avahi/$', AppView.as_view(app_id='avahi'), name='index'),
]
