# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Configuration module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/config/$', views.ConfigAppView.as_view(), name='index'),
]
