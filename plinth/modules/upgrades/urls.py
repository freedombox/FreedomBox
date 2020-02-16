# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the upgrades module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/upgrades/$', views.UpgradesConfigurationView.as_view(),
        name='index'),
    url(r'^sys/upgrades/upgrade/$', views.upgrade, name='upgrade'),
]
