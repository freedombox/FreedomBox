# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the mldonkey module.
"""

from django.urls import re_path

from plinth.views import AppView

urlpatterns = [
    re_path(r'^apps/mldonkey/$', AppView.as_view(app_id='mldonkey'),
            name='index')
]
