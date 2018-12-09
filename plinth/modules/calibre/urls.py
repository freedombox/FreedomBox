# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the calibre module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^apps/calibre/$', views.CalibreAppView.as_view(), name='index'),
    url(r'^apps/calibre/library/create/$', views.CreateLibraryView.as_view(),
        name='create-library'),
    url(r'^apps/calibre/library/(?P<name>[a-zA-Z0-9_.-]+)/delete/$',
        views.delete_library, name='delete-library'),
]
