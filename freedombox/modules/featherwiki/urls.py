# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the Feather Wiki app."""

from django.urls import re_path

from .views import (CreateWikiView, FeatherWikiAppView, RenameWikiView,
                    UploadWikiView, delete)

urlpatterns = [
    re_path(r'^apps/featherwiki/$', FeatherWikiAppView.as_view(),
            name='index'),
    re_path(r'^apps/featherwiki/create/$', CreateWikiView.as_view(),
            name='create'),
    re_path(r'^apps/featherwiki/upload/$', UploadWikiView.as_view(),
            name='upload'),
    re_path(r'^apps/featherwiki/(?P<old_name>.+\.html)/rename/$',
            RenameWikiView.as_view(), name='rename'),
    re_path(r'^apps/featherwiki/(?P<name>.+\.html)/delete/$', delete,
            name='delete'),
]
