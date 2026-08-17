# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the security module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/security/$', views.SecurityAppView.as_view(), name='index'),
    re_path(r'^sys/security/report$', views.report, name='report'),
]
