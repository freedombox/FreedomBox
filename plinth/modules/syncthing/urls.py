# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Syncthing module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^apps/syncthing/$', AppView.as_view(app_id='syncthing'),
        name='index')
]
