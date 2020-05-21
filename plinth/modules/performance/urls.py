# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for System Monitoring (cockpit-pcp) in ‘System’.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^sys/performance/$', AppView.as_view(app_id='performance'),
        name='index'),
]
