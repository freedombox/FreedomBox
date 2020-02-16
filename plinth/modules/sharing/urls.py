# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the sharing app.
"""

from django.conf.urls import url

from .views import AddShareView, EditShareView, IndexView, remove

urlpatterns = [
    url(r'^apps/sharing/$', IndexView.as_view(), name='index'),
    url(r'^apps/sharing/add/$', AddShareView.as_view(), name='add'),
    url(r'^apps/sharing/(?P<name>[a-z0-9]+)/edit/$', EditShareView.as_view(),
        name='edit'),
    url(r'^apps/sharing/(?P<name>[a-z0-9]+)/remove/$', remove, name='remove'),
]
