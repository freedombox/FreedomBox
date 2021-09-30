# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for System Monitoring (cockpit-pcp) in ‘System’.
"""

from django.urls import re_path

from plinth.views import AppView

urlpatterns = [
    re_path(r'^sys/performance/$', AppView.as_view(app_id='performance'),
            name='index'),
]
