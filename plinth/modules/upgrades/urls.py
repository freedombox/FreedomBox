# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the upgrades module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/upgrades/$', views.UpgradesConfigurationView.as_view(),
            name='index'),
    re_path(r'^sys/upgrades/activate-backports/$', views.activate_backports,
            name='activate-backports'),
    re_path(r'^sys/upgrades/firstboot/backports/$',
            views.BackportsFirstbootView.as_view(),
            name='backports-firstboot'),
    re_path(r'^sys/upgrades/upgrade/$', views.upgrade, name='upgrade'),
    re_path(r'^sys/upgrades/test-dist-upgrade/$', views.test_dist_upgrade,
            name='test-dist-upgrade'),
]
