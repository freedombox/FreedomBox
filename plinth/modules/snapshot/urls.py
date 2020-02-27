# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the snapshot module.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/snapshot/$', views.index, name='index'),
    url(r'^sys/snapshot/manage/$', views.manage, name='manage'),
    url(r'^sys/snapshot/selected/delete$', views.delete_selected,
        name='delete-selected'),
    url(r'^sys/snapshot/(?P<number>\d+)/rollback$', views.rollback,
        name='rollback'),
]
