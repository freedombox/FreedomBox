# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Configuration module
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sys/config/$', views.ConfigAppView.as_view(), name='index'),
]
