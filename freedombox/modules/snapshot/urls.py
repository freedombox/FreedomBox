# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the snapshot module.
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/snapshot/$', views.SnapshotAppView.as_view(), name='index'),
    re_path(r'^sys/snapshot/manage/$', views.manage, name='manage'),
    re_path(r'^sys/snapshot/selected/delete$', views.delete_selected,
            name='delete-selected'),
    re_path(r'^sys/snapshot/(?P<number>\d+)/rollback$', views.rollback,
            name='rollback'),
]
