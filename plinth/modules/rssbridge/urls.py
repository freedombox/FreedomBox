# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the RSS-Bridge module.
"""

from django.urls import re_path

from plinth.views import AppView

urlpatterns = [
    re_path(r'^apps/rssbridge/$', AppView.as_view(app_id='rssbridge'),
            name='index'),
]
