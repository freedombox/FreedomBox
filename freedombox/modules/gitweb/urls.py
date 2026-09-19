# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Gitweb module.
"""

from django.urls import re_path

from .views import CreateRepoView, EditRepoView, GitwebAppView, delete

urlpatterns = [
    re_path(r'^apps/gitweb/$', GitwebAppView.as_view(), name='index'),
    re_path(r'^apps/gitweb/create/$', CreateRepoView.as_view(), name='create'),
    re_path(
        r'^apps/gitweb/(?P<name>[a-zA-Z0-9-._]+)/edit/$',
        EditRepoView.as_view(),
        name='edit',
    ),
    re_path(
        r'^apps/gitweb/(?P<name>[a-zA-Z0-9-._]+)/delete/$',
        delete,
        name='delete',
    ),
]
