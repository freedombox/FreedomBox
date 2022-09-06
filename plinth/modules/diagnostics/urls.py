# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Diagnostics module
"""

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^sys/diagnostics/$', views.DiagnosticsView.as_view(),
            name='index'),
    re_path(r'^sys/diagnostics/(?P<app_id>[1-9a-z\-_]+)/$', views.diagnose_app,
            name='app'),
]
