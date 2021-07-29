# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the WordPress module.
"""

from django.conf.urls import url

from .views import WordPressAppView

urlpatterns = [
    url(r'^apps/wordpress/$', WordPressAppView.as_view(app_id='wordpress'),
        name='index'),
]
