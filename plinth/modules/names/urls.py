# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the name services module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/names/$', views.NamesAppView.as_view(), name='index'),
    re_path(r'^sys/names/hostname/$', views.HostnameView.as_view(),
            name='hostname'),
    re_path(r'^sys/names/domains/$', views.DomainNameView.as_view(),
            name='domains'),
]
