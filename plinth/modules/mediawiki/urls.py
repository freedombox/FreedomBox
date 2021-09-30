# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the mediawiki module.
"""

from django.urls import re_path

from .views import MediaWikiAppView

urlpatterns = [
    re_path(r'^apps/mediawiki/$', MediaWikiAppView.as_view(), name='index'),
]
