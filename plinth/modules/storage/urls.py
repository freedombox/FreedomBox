# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the disks module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/storage/$', views.StorageAppView.as_view(), name='index'),
    re_path(r'^sys/storage/expand$', views.expand, name='expand'),
    re_path(r'^sys/storage/eject/(?P<device_path>[A-Za-z0-9%_.\-~]+)/$',
            views.eject, name='eject')
]
