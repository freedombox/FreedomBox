# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the infinoted module.
"""

from django.urls import re_path

from plinth.views import AppView

urlpatterns = [
    re_path(r'^apps/infinoted/$', AppView.as_view(app_id='infinoted'),
            name='index'),
]
