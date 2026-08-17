# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the TiddlyWiki app."""

from django.urls import re_path

from .views import (CreateWikiView, TiddlyWikiAppView, RenameWikiView,
                    UploadWikiView, delete)

urlpatterns = [
    re_path(r'^apps/tiddlywiki/$', TiddlyWikiAppView.as_view(),
            name='index'),
    re_path(r'^apps/tiddlywiki/create/$', CreateWikiView.as_view(),
            name='create'),
    re_path(r'^apps/tiddlywiki/upload/$', UploadWikiView.as_view(),
            name='upload'),
    re_path(r'^apps/tiddlywiki/(?P<old_name>.+\.html)/rename/$',
            RenameWikiView.as_view(), name='rename'),
    re_path(r'^apps/tiddlywiki/(?P<name>.+\.html)/delete/$', delete,
            name='delete'),
]
