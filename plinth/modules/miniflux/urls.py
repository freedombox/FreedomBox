# SPDX-License-Identifier: AGPL-3.0-or-later
"""URLs for the Miniflux module."""

from django.urls import re_path

from .views import CreateAdminUserView, MinifluxAppView, ResetUserPasswordView

urlpatterns = [
    re_path(r'^apps/miniflux/$', MinifluxAppView.as_view(), name='index'),
    re_path(r'^apps/miniflux/create-admin-user/$',
            CreateAdminUserView.as_view(), name='create-admin-user'),
    re_path(r'^apps/miniflux/reset-user-password/$',
            ResetUserPasswordView.as_view(), name='reset-user-password'),
]
