# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the disks module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/storage/$', views.StorageAppView.as_view(), name='index'),
    url(r'^sys/storage/expand$', views.expand, name='expand'),
    url(r'^sys/storage/eject/(?P<device_path>[A-Za-z0-9%_.\-~]+)/$',
        views.eject, name='eject')
]
