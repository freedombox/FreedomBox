# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Shaarli module.
"""

from django.urls import re_path

from plinth.views import AppView

urlpatterns = [
    re_path(r'^apps/shaarli/$', AppView.as_view(app_id='shaarli'),
            name='index')
]
