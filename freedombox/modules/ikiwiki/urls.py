# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the ikiwiki module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^apps/ikiwiki/$', views.IkiwikiAppView.as_view(), name='index'),
    re_path(r'^apps/ikiwiki/(?P<name>.+)/delete/$', views.delete,
            name='delete'),
    re_path(r'^apps/ikiwiki/create/$', views.create, name='create'),
]
