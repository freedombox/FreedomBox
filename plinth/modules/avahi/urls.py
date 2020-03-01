# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the service discovery module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^sys/avahi/$', AppView.as_view(app_id='avahi'), name='index'),
]
