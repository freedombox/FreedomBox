# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Kiwix module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^apps/kiwix/$', views.KiwixAppView.as_view(), name='index'),
    re_path(r'^apps/kiwix/content/add/$', views.AddContentView.as_view(),
            name='add-content'),
    re_path(r'^apps/kiwix/content/(?P<zim_id>[a-zA-Z0-9-]+)/delete/$',
            views.delete_content, name='delete-content'),
]
