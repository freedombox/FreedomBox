# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the WordPress module.
"""

from django.urls import re_path

from .views import WordPressAppView

urlpatterns = [
    re_path(r'^apps/wordpress/$', WordPressAppView.as_view(app_id='wordpress'),
            name='index'),
]
