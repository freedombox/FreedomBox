# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Gitweb module.
"""

from django.conf.urls import url

from .views import CreateRepoView, EditRepoView, GitwebAppView, delete

urlpatterns = [
    url(r'^apps/gitweb/$', GitwebAppView.as_view(), name='index'),
    url(r'^apps/gitweb/create/$', CreateRepoView.as_view(), name='create'),
    url(
        r'^apps/gitweb/(?P<name>[a-zA-Z0-9-._]+)/edit/$',
        EditRepoView.as_view(),
        name='edit',
    ),
    url(
        r'^apps/gitweb/(?P<name>[a-zA-Z0-9-._]+)/delete/$',
        delete,
        name='delete',
    ),
]
