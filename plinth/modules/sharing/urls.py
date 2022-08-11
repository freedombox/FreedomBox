# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the sharing app.
"""

from django.urls import re_path

from .views import AddShareView, EditShareView, SharingAppView, remove

urlpatterns = [
    re_path(r'^apps/sharing/$', SharingAppView.as_view(), name='index'),
    re_path(r'^apps/sharing/add/$', AddShareView.as_view(), name='add'),
    re_path(r'^apps/sharing/(?P<name>[a-z0-9]+)/edit/$',
            EditShareView.as_view(), name='edit'),
    re_path(r'^apps/sharing/(?P<name>[a-z0-9]+)/remove/$', remove,
            name='remove'),
]
