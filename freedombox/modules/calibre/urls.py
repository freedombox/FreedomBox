# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the calibre module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^apps/calibre/$', views.CalibreAppView.as_view(), name='index'),
    re_path(r'^apps/calibre/library/create/$',
            views.CreateLibraryView.as_view(), name='create-library'),
    re_path(r'^apps/calibre/library/(?P<name>[a-zA-Z0-9_.-]+)/delete/$',
            views.delete_library, name='delete-library'),
]
