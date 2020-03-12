# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Tiny Tiny RSS module.
"""

from django.conf.urls import url

from plinth.views import AppView

urlpatterns = [
    url(r'^apps/ttrss/$', AppView.as_view(app_id='ttrss'), name='index')
]
