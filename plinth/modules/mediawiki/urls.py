# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the mediawiki module.
"""

from django.conf.urls import url

from .views import MediaWikiAppView

urlpatterns = [
    url(r'^apps/mediawiki/$', MediaWikiAppView.as_view(), name='index'),
]
