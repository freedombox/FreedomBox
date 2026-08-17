# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the RSS-Bridge module.
"""

from django.urls import re_path

from .views import RSSBridgeAppView

urlpatterns = [
    re_path(r'^apps/rssbridge/$', RSSBridgeAppView.as_view(app_id='rssbridge'),
            name='index'),
]
